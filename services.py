import asyncio
import json
import string
import ast
import re
from typing import Tuple, Optional
from loguru import logger
from typing import Any, Optional

from .message_builder import MessageBundle, build_message as _build_message, validate_pubkey_hex
from .utils import get_random_goat_names, join_with_and

_nostrclient_check_lock = asyncio.Lock()
_nostrclient_available: Optional[bool] = None


def normalize_relay_hint(raw: str | None) -> str | None:
    """Normalize a raw relay string into a websocket URL or return None.

    Maps http(s) -> ws(s) and accepts ws:// or wss:// as-is.
    Returns None for non-matching inputs.
    """
    if not raw:
        return None
    try:
        s = str(raw).strip()
        if not s:
            return None
        if s.startswith("wss://") or s.startswith("ws://"):
            return s
        if s.startswith("https://"):
            return "wss://" + s[len("https://") :]
        if s.startswith("http://"):
            return "ws://" + s[len("http://") :]
        return None
    except Exception:
        return None


async def _is_nostrclient_available() -> bool:
    """Private helper: check if nostrclient extension is importable (cached).
    
    Returns:
        True if nostrclient is available, False otherwise.
    """
    global _nostrclient_available
    if _nostrclient_available is not None:
        return _nostrclient_available

    async with _nostrclient_check_lock:
        if _nostrclient_available is not None:
            return _nostrclient_available

        try:
            from lnbits.extensions.nostrclient.router import nostr_client  # type: ignore  # noqa: F401

            _nostrclient_available = True
        except Exception as exc:  # pragma: no cover - optional dependency path
            _nostrclient_available = False
            logger.warning(
                "cyberherd_messaging: nostrclient extension unavailable, disabling nostr publishing (%s)",
                exc,
            )
        return _nostrclient_available


async def send_to_websocket_clients(topic: str, message: dict) -> bool:
    """Broadcast a message to all WebSocket clients subscribed to a topic.
    
    Args:
        topic: The WebSocket item_id/topic (e.g., "cyberherd")
        message: Dictionary payload to send (will be JSON-serialized)
    
    Returns:
        True if message was sent successfully, False otherwise
    """
    try:
        from lnbits.core.services.websockets import websocket_updater
        
        # Serialize the message to JSON
        payload = json.dumps(message)
        
        # Send to all connected clients on this topic
        await websocket_updater(topic, payload)
        
        logger.debug(f"WebSocket message sent to topic '{topic}': {message.get('type', 'unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket message to topic '{topic}': {e}")
        return False


async def is_nostr_publishing_enabled() -> bool:
    """Return True if nostr publishing is enabled and available.

    Checks two conditions:
    1. The nostr_publishing_enabled setting (from database)
    2. The nostrclient extension availability (cached)

    If the setting is disabled (0/false/no/off), returns False immediately.
    Otherwise returns the nostrclient availability status.
    
    Missing database rows are treated as "enabled" (backward compatible default).
    Database errors fall back to True with a warning.
    """
    # Check the database setting first
    try:
        # Lazy import to avoid circular dependency
        from . import crud
        
        setting_value = await crud.get_setting("nostr_publishing_enabled")
        
        if setting_value is not None:
            # Normalize the value (trim whitespace, lowercase)
            normalized = str(setting_value).strip().lower()
            
            # Check for disabled states: 0, false, no, off
            if normalized in ("0", "false", "no", "off", ""):
                logger.info("cyberherd_messaging: nostr publishing disabled by setting (nostr_publishing_enabled=%s)", normalized)
                return False
            
            logger.debug("cyberherd_messaging: nostr publishing enabled by setting (nostr_publishing_enabled=%s)", normalized)
        else:
            # Missing DB row = enabled (backward compatible default)
            logger.debug("cyberherd_messaging: nostr_publishing_enabled setting not found, defaulting to enabled")
            
    except Exception as exc:
        # Database error - fall back to enabled but warn
        logger.warning(
            "cyberherd_messaging: failed to read nostr_publishing_enabled setting, defaulting to enabled (%s)",
            exc,
        )
    
    # If setting is enabled (or missing/errored), check nostrclient availability
    return await _is_nostrclient_available()


def _prepare_private_key(raw_value: str | None) -> tuple[str | None, int, Exception | None]:
    """Normalize private key material and return (hex_key, length, error)."""
    if not raw_value:
        return None, 0, None

    candidate = (raw_value or "").strip()
    candidate = "".join(candidate.split())  # drop whitespace/newlines

    try:
        from lnbits.utils.nostr import normalize_private_key

        normalized = normalize_private_key(candidate)
    except Exception as exc:
        return None, 0, exc

    if not normalized:
        return None, 0, ValueError("normalize_private_key returned empty value")

    if normalized.startswith("0x"):
        normalized = normalized[2:]

    hex_only = "".join(ch for ch in normalized if ch in string.hexdigits).lower()
    sanitized_len = len(hex_only)

    if sanitized_len >= 64:
        return hex_only[:64], sanitized_len, None

    return None, sanitized_len, ValueError(f"invalid length {sanitized_len}")


def create_and_sign_event(content: str, private_key_hex: str, tags: list[tuple[str, str]]):
    """Create and sign a Nostr event using LNbits built-in nostrclient.
    
    Args:
        content: The note content
        private_key_hex: The private key as a hex string (64 chars)
        tags: List of (tag_name, tag_value) tuples
        
    Returns:
        Signed Event object
        
    Raises:
        RuntimeError: If nostrclient components are not available
    """
    try:
        from lnbits.extensions.nostrclient.nostr.event import Event
        from lnbits.extensions.nostrclient.nostr.key import PrivateKey
    except ImportError as e:
        raise RuntimeError(f"nostrclient not installed or unavailable: {e}")

    try:
        import secp256k1  # type: ignore
    except Exception as e:
        raise RuntimeError(f"secp256k1 not installed: {e}")

    # Create private key object and extract public key
    privkey_obj = PrivateKey(bytes.fromhex(private_key_hex))
    pubkey = privkey_obj.public_key.hex()

    # Use kind 1311 for 30311 replies, kind 1 for regular posts
    has_30311_tags = any(
        isinstance(tag, (list, tuple))
        and len(tag) >= 2
        and tag[0] == "a"
        and str(tag[1]).startswith("30311:")
        for tag in (tags or [])
    )
    kind = 1311 if has_30311_tags else 1

    # Create the event
    formatted_tags = []
    for tag in tags or []:
        if isinstance(tag, (list, tuple)):
            formatted_tags.append([str(part) for part in tag])
        else:
            formatted_tags.append([str(tag)])

    evt = Event(
        content=content,
        public_key=pubkey,
        kind=kind,
        tags=formatted_tags,
    )
    
    # Sign the event (sets evt.signature)
    privkey_obj.sign_event(evt)
    
    logger.debug(
        f"cyberherd_messaging: created and signed kind {kind} event {evt.id[:8]}... "
        f"with {len(tags or [])} tags"
    )
    
    return evt



async def publish_note(
    content: str,
    *,
    tags: list[tuple[str, str]] | None = None,
    e_tags: list[str] | None = None,
    p_tags: list[str] | None = None,
    private_key_hex: str | None = None,
    reply_to_30311_event: str | None = None,
    reply_to_30311_a_tag: str | None = None,
    reply_relay: str | None = None,
) -> bool:
    """Publish a nostr note via in-process nostrclient only.

    - Requires private_key_hex to sign locally.
    - Supports e_tags (reply threading), p_tags (mentions), and arbitrary tags.
    """
    enabled = await is_nostr_publishing_enabled()
    if not enabled:
        return True

    # Merge convenience tags with NIP-10 markers and deduplication
    all_tags: list[tuple[str, ...]] = []
    seen_tags: set[tuple[str, ...]] = set()

    def _add_tag(parts: tuple[str, ...]) -> None:
        normalized = tuple("" if part is None else str(part) for part in parts)
        if not normalized:
            return
        if normalized in seen_tags:
            return
        seen_tags.add(normalized)
        all_tags.append(normalized)

    for tag in tags or []:
        if isinstance(tag, (list, tuple)):
            _add_tag(tuple("" if part is None else str(part) for part in tag))
        else:
            _add_tag((str(tag),))

    normalized_e_ids: list[str] = []
    normalized_p_ids: list[str] = []

    def _append_unique(target: list[str], candidate: str | None) -> None:
        if not isinstance(candidate, str):
            return
        value = candidate.strip()
        if not value:
            return
        if value not in target:
            target.append(value)

    for e_id in e_tags or []:
        _append_unique(normalized_e_ids, e_id)

    # Normalize reply_relay once for use when embedding relay hints into e-tags
    normalized_reply = normalize_relay_hint(reply_relay)

    if reply_to_30311_event:
        _append_unique(normalized_e_ids, reply_to_30311_event)

    for p_id in p_tags or []:
        _append_unique(normalized_p_ids, p_id)

    # Validate and filter p_tags to ensure they're valid hex pubkeys
    validated_p_ids: list[str] = []
    for p_id in normalized_p_ids:
        if not p_id:
            continue
        # Import validation function
        from .message_builder import validate_pubkey_hex
        if validate_pubkey_hex(p_id):
            validated_p_ids.append(p_id.strip().lower())
        else:
            logger.debug(f"Invalid pubkey in p_tags, skipping: {p_id[:20] if len(p_id) > 20 else p_id}")
    
    has_reply_context = bool(reply_to_30311_event or e_tags)

    if normalized_e_ids:
        relay_hint = normalized_reply or ""
        root_id = normalized_e_ids[0]
        
        # NIP-10 compliance: For direct replies to root (single event id),
        # use only "root" marker. For replies with intermediate events,
        # mark first as "root" and direct parent as "reply".
        if len(normalized_e_ids) == 1:
            # Direct reply to root - single "root" marker per NIP-10
            _add_tag(("e", root_id, relay_hint, "root"))
        else:
            # Reply chain with multiple events
            _add_tag(("e", root_id, relay_hint, "root"))
            reply_id = normalized_e_ids[1]
            _add_tag(("e", reply_id, relay_hint, "reply"))
            
            # Additional events are mentions
            for e_id in normalized_e_ids[2:]:
                _add_tag(("e", e_id, "", "mention"))

    # Add validated p_tags
    for p_id in validated_p_ids:
        _add_tag(("p", p_id))

    if reply_to_30311_a_tag:
        candidate = reply_to_30311_a_tag.strip() if isinstance(reply_to_30311_a_tag, str) else None
        if candidate:
            _add_tag(("a", candidate))

    priv_len = len(private_key_hex) if isinstance(private_key_hex, str) else 0
    logger.debug(
        f"cyberherd_messaging: publish_note content_len={len(content or '')} "
        f"e_tags={len(e_tags or [])} p_tags={len(p_tags or [])} private_key_len={priv_len}"
    )

    sanitized_key = private_key_hex
    sanitized_len = priv_len
    if private_key_hex and priv_len != 64:
        sanitized_key, sanitized_len, sanitize_err = _prepare_private_key(private_key_hex)
        if sanitize_err:
            logger.info(
                f"cyberherd_messaging: skipping note publish because signing failed ({sanitize_err})"
            )
            return False
        logger.debug(
            f"cyberherd_messaging: sanitized private key len={sanitized_len}"
        )

    if not sanitized_key:
        logger.warning("publish_note called without private_key_hex; skipping")
        return False

    try:
        signed_event = create_and_sign_event(content, sanitized_key, all_tags)
    except RuntimeError as exc:
        logger.error(
            f"cyberherd_messaging: failed to create/sign event: {type(exc).__name__}: {exc}"
        )
        return False
    except Exception as exc:
        logger.error(
            f"cyberherd_messaging: unexpected error creating/signing event: "
            f"{type(exc).__name__}: {exc}"
        )
        return False

    try:
        from lnbits.extensions.nostrclient.router import nostr_client

        if not hasattr(nostr_client, 'relay_manager'):
            logger.warning("cyberherd_messaging: nostr_client has no relay_manager")
            return False
            
        # Convert Event object to message format and publish
        event_message = signed_event.to_message()
        nostr_client.relay_manager.publish_message(event_message)
        
        logger.info(
            f"cyberherd_messaging: ✅ published kind {signed_event.kind} event "
            f"{signed_event.id[:8]}... to {len(nostr_client.relay_manager.relays)} relays"
        )
        logger.debug(
            "publish_note success details: content=%s e_tags=%s p_tags=%s tags=%s",
            content[:200] if content else None,
            e_tags,
            p_tags,
            all_tags,
        )
        return True
        
    except Exception as e:
        logger.error(
            f"cyberherd_messaging: ❌ nostrclient publish failed: {type(e).__name__}: {e}"
        )
        return False


async def try_publish_note(
    content: str,
    *,
    e_tags: list[str] | None = None,
    p_tags: list[str] | None = None,
    private_key: str | None = None,
    reply_relay: str | None = None,
) -> bool:
    """Alias for publish_note with different parameter naming."""
    key_hex, key_len, key_error = _prepare_private_key(private_key)

    logger.info(
        f"cyberherd_messaging: try_publish_note content_len={len(content or '')} "
        f"e_tags={e_tags} p_tags={p_tags} private_key_len={key_len}"
    )

    if key_error:
        logger.info(
            f"cyberherd_messaging: skipping note publish because signing failed ({key_error})"
        )
        return False

    return await publish_note(
        content,
        e_tags=e_tags,
        p_tags=p_tags,
        private_key_hex=key_hex,
        reply_relay=reply_relay,
    )


def _coerce_int(value: Any, default: int = 0) -> int:
    """Best-effort conversion to int, preserving default on failure."""
    if value is None:
        return default
    try:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except Exception:
        return default


def _normalize_goat_data(raw: Any) -> list[dict[str, str]] | None:
    """Return a standardized [{name, imageUrl}] list for various goat payload formats."""
    if not raw:
        return None

    result: list[dict[str, str]] = []

    def _fallback_image(name: str | None) -> str:
        if not name:
            return ""
        slug = "".join(ch for ch in str(name).lower() if ch.isalnum())
        return f"images/{slug}.png" if slug else ""

    if isinstance(raw, (list, tuple, set)):
        iterable = list(raw)
    else:
        iterable = [raw]

    for item in iterable:
        if not item:
            continue
        if isinstance(item, dict):
            name = (
                item.get("name")
                or item.get("display_name")
                or item.get("member_name")
                or item.get("username")
                or ""
            )
            image = (
                item.get("imageUrl")
                or item.get("image_url")
                or item.get("picture")
                or item.get("avatar")
                or ""
            )
            if not image:
                image = _fallback_image(name)
            if name or image:
                result.append({"name": str(name or "Goat"), "imageUrl": str(image)})
            continue

        if isinstance(item, (list, tuple)):
            name = str(item[0]) if item else ""
            image = ""
            if len(item) > 3 and isinstance(item[3], str):
                image = item[3]
            if not image:
                image = _fallback_image(name)
            result.append({"name": name or "Goat", "imageUrl": image})
            continue

        if isinstance(item, str):
            result.append({"name": item, "imageUrl": _fallback_image(item)})

    return result or None


async def _augment_membership_rendered_content(
    base_content: str,
    values: dict[str, Any],
    *,
    reply_to_30311_event: str | None,
    reply_to_30311_a_tag: str | None,
    template_overrides: Optional[dict[str, dict[str, Any]]] = None,
) -> tuple[str, MessageBundle | None]:
    """Append supplemental membership info (spots/headbutt text) when available."""
    try:
        event_type = values.get("_semantic_event_type") or values.get("event_type") or values.get("type")
        if not isinstance(event_type, str):
            return base_content, None
        event_type = event_type.strip()
        if event_type not in {"cyber_herd", "new_member"}:
            return base_content, None

        ch_item = values.get("cyber_herd_item") if isinstance(values.get("cyber_herd_item"), dict) else {}
        ch_item = dict(ch_item)  # shallow copy so we can augment safely

        display_name = (
            values.get("member_display_name")
            or values.get("display_name")
            or values.get("name")
            or ch_item.get("display_name")
            or "Anon"
        )
        ch_item.setdefault("display_name", display_name)
        ch_item.setdefault("pubkey", values.get("member_pubkey") or values.get("pubkey") or ch_item.get("pubkey"))
        ch_item.setdefault("nprofile", values.get("member_nprofile") or values.get("nprofile") or ch_item.get("nprofile"))
        ch_item.setdefault("event_id", values.get("event_id") or values.get("note_id") or ch_item.get("event_id"))

        amount_candidate = ch_item.get("amount")
        if amount_candidate is None:
            for key in ("initial_amount", "new_amount", "amount", "increase_amount"):
                if values.get(key) is not None:
                    amount_candidate = values.get(key)
                    break
        ch_item["amount"] = _coerce_int(amount_candidate, 0)

        if "headbutt_info" in values and values.get("headbutt_info"):
            try:
                if isinstance(values.get("headbutt_info"), dict):
                    ch_item.setdefault("headbutt_info", dict(values.get("headbutt_info")))
            except Exception:
                ch_item.setdefault("headbutt_info", values.get("headbutt_info"))

        difference = values.get("difference", 0)
        new_amount = values.get("new_amount")
        if new_amount is None:
            new_amount = values.get("initial_amount", ch_item.get("amount", 0))

        spots_remaining = values.get("spots_remaining", values.get("_spots_remaining", 0))
        spots_remaining = _coerce_int(spots_remaining, 0)

        relays = values.get("relays")

        bundle = await _build_message(
            event_type,
            new_amount=_coerce_int(new_amount, 0),
            difference=_coerce_int(difference, 0),
            cyber_herd_item=ch_item,
            spots_remaining=spots_remaining,
            relays=relays,
            reply_to_30311_event=reply_to_30311_event,
            reply_to_30311_a_tag=reply_to_30311_a_tag,
            template_overrides=template_overrides,
        )
        extras = (bundle.spots_info or "") + (bundle.headbutt_text or "")
        if extras:
            return (base_content or "") + extras, bundle
        return base_content, bundle
    except Exception as exc:
        logger.debug("cyberherd_messaging: failed to augment membership message: %s", exc)
        return base_content, None


async def render_and_publish_template(
    *,
    user_id: str,
    category: str,
    key: str,
    values: dict[str, Any] | None = None,
    e_tags: list[str] | None = None,
    p_tags: list[str] | None = None,
    private_key: str | None = None,
    reply_to_30311_event: str | None = None,
    reply_to_30311_a_tag: str | None = None,
    reply_relay: str | None = None,
    return_websocket_message: bool = False,
):
    """Render a template with values and publish as nostr note, or return for websocket.

    - Retrieves template from database using user_id, category, key
    - Renders template with provided values
    - If return_websocket_message is True, returns (rendered_content, goat_data) for websocket use
    - Otherwise publishes to nostr and returns success bool
    """
    from . import crud
    
    # Get the template from database
    template_obj = await crud.get_message_template(user_id, category, key)
    if not template_obj:
        logger.error(f"Template not found: user_id={user_id}, category={category}, key={key}")
        if return_websocket_message:
            return ("", [])
        return False
    
    # Template content may itself be a serialized dict string (JSON or Python literal)
    def _extract_content_and_reply(raw: Any) -> Tuple[str, Optional[str]]:
        """Return (content_string, reply_relay) when template content may be a serialized dict.

        Accepts:
        - dict -> returns content/reply_relay
        - JSON string
        - Python literal (single-quoted dict)
        - JSON-like string with single quotes (attempts safe replace)
        - Falls back to regex extraction of 'content' and 'reply_relay' keys
        """
        if isinstance(raw, dict):
            return (raw.get("content") or "", raw.get("reply_relay"))
        if not isinstance(raw, str):
            return (str(raw or ""), None)

        s = raw.strip()

        # Try JSON first
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict) and "content" in parsed:
                return (parsed.get("content") or "", parsed.get("reply_relay"))
        except Exception:
            pass

        # Fallback to Python literal parsing (single-quoted dicts)
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, dict) and "content" in parsed:
                return (str(parsed.get("content") or ""), parsed.get("reply_relay"))
        except Exception:
            pass

        # Try a safe single-quote -> double-quote replacement for JSON-like strings
        # but only if it looks like a simple dict (starts with { and ends with })
        if s.startswith("{") and s.endswith("}"):
            try:
                s2 = s.replace("'", '"')
                parsed = json.loads(s2)
                if isinstance(parsed, dict) and "content" in parsed:
                    return (parsed.get("content") or "", parsed.get("reply_relay"))
            except Exception:
                pass

        # Fallback: regex extraction for content and reply_relay fields
        try:
            # content may contain escaped newlines \n etc.; capture lazily
            # First attempt: strict quoted extraction
            m = re.search(r"['\"]content['\"]\s*:\s*['\"](.*?)['\"]\s*(?:,|})", s, flags=re.DOTALL)
            r = None
            if m:
                r = m.group(1)
                # Unescape common sequences like \n
                try:
                    r = bytes(r, "utf-8").decode("unicode_escape")
                except Exception:
                    pass

            m2 = re.search(r"['\"]reply_relay['\"]\s*:\s*['\"](.*?)['\"]\s*(?:,|})", s, flags=re.DOTALL)
            rr = m2.group(1) if m2 else None
            if rr:
                rr = rr.strip()

            if r:
                return (r, rr)

            # Looser fallback: handle cases where quoting is inconsistent
            # e.g., content: 'some text', or content: some text,
            m_loose = re.search(r"content\s*:\s*(['\"]?)(.*?)\1\s*(?:,|})", s, flags=re.DOTALL)
            rr_loose = re.search(r"reply_relay\s*:\s*(['\"]?)(.*?)\1\s*(?:,|})", s, flags=re.DOTALL)
            r2 = None
            if m_loose:
                candidate = m_loose.group(2)
                if candidate:
                    try:
                        candidate = bytes(candidate, "utf-8").decode("unicode_escape")
                    except Exception:
                        pass
                    r2 = candidate.strip()

            rr2 = None
            if rr_loose:
                rr2 = rr_loose.group(2).strip()

            if r2:
                return (r2, rr2)
        except Exception:
            pass

        # Nothing matched. If the raw string looks like a dict (e.g. "{...:...}")
        # we should NOT publish it verbatim as kind=1 content. Return an empty
        # content string and log a warning so callers avoid creating non-compliant
        # notes. Otherwise return the raw string.
        looks_like_dict = s.startswith("{") and s.endswith("}") and ":" in s
        if looks_like_dict:
            logger.warning(
                "cyberherd_messaging: template content appears to be a serialized dict and was discarded to avoid publishing raw structured data: %s",
                (s[:200] + "...") if len(s) > 200 else s,
            )
            return ("", None)

        return (s, None)

    template_content_raw = template_obj.content
    tpl_content, tpl_reply = _extract_content_and_reply(template_content_raw)
    template_content = tpl_content
    values = values or {}
    
    # Prepare goat name substitutions when required
    goat_data_bundle = None
    template_str = template_content
    if template_content and "{goat_name}" in str(template_content):
        template_str = str(template_content)

        def _normalize_profile(val: str | None) -> str:
            if not val:
                return ""
            val = str(val)
            return val if val.startswith("nostr:") else f"nostr:{val}"

        bundle = values.get("_goat_bundle") if isinstance(values, dict) else None
        if not bundle:
            raw_goats = get_random_goat_names()
            names = [str(name) for name, *_ in raw_goats]
            profiles = [_normalize_profile(profile) for _, profile, *_ in raw_goats]
            bundle = {
                "raw": raw_goats,
                "names": join_with_and(names),
                "profiles": join_with_and(profiles),
            }
            if isinstance(values, dict):
                values["_goat_bundle"] = bundle
        goat_data_bundle = bundle.get("raw") if isinstance(bundle, dict) else None
        if return_websocket_message:
            if isinstance(values, dict):
                # Use display names for websocket rendering without mutating original values
                temp_values = dict(values)
                temp_values["goat_name"] = bundle.get("names", "")
                values = temp_values
        else:
            if isinstance(values, dict):
                # Force-set goat_name to nprofiles for Nostr messages
                values["goat_name"] = bundle.get("profiles", "")

    # Render the template
    try:
        rendered_content = str(template_str).format(**values)
    except Exception as e:
        logger.error(f"Template render failed: {e}")
        if return_websocket_message:
            return ("", [])
        return False

    augmented_bundle: MessageBundle | None = None
    if isinstance(values, dict):
        # Try to load template overrides for this user so the builder prefers DB templates
        template_overrides = {}
        try:
            template_overrides = await _load_template_overrides(values.get("user_id") or values.get("owner_id") or None)
        except Exception:
            template_overrides = {}

        rendered_content, augmented_bundle = await _augment_membership_rendered_content(
            rendered_content,
            values,
            reply_to_30311_event=reply_to_30311_event,
            reply_to_30311_a_tag=reply_to_30311_a_tag,
            template_overrides=template_overrides,
        )
    
    if return_websocket_message:
        goat_data = None
        if augmented_bundle and augmented_bundle.goat_data:
            goat_data = augmented_bundle.goat_data
        elif goat_data_bundle:
            goat_data = _normalize_goat_data(goat_data_bundle)
        return (rendered_content, goat_data)
    
    # Publish to nostr
    # Extract goat pubkeys and add to p_tags for proper Nostr tagging
    goat_p_tags = []
    if goat_data_bundle:
        # goat_data_bundle is raw goats from get_random_goat_names(): [(name, profile, pubkey), ...]
        for item in goat_data_bundle:
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                pubkey_hex = item[2]  # Third element is the pubkey hex
                if pubkey_hex and isinstance(pubkey_hex, str):
                    # Use enhanced validation from message_builder
                    if validate_pubkey_hex(pubkey_hex):
                        goat_p_tags.append(pubkey_hex.strip().lower())
                    else:
                        logger.debug(
                            f"Invalid goat pubkey format, skipping: {pubkey_hex[:20]}..."
                        )
    
    # Merge goat p_tags with existing p_tags (normalize and deduplicate)
    combined_p_tags = list(p_tags or [])
    for goat_pubkey in goat_p_tags:
        # Normalize existing p_tags for comparison
        normalized_existing = [p.strip().lower() for p in combined_p_tags]
        if goat_pubkey not in normalized_existing:
            combined_p_tags.append(goat_pubkey)
    
    # Normalize template-provided reply_relay if present
    tpl_reply_norm = normalize_relay_hint(tpl_reply) if tpl_reply else None
    if tpl_reply and not tpl_reply_norm:
        logger.warning(
            "cyberherd_messaging: template reply_relay '%s' is not a ws/wss URL and was ignored",
            tpl_reply,
        )

    effective_reply_relay = reply_relay or tpl_reply_norm or normalize_relay_hint(getattr(template_obj, "reply_relay", None))

    return await publish_note(
        rendered_content,
        e_tags=e_tags,
        p_tags=combined_p_tags,
        private_key_hex=private_key,
        reply_to_30311_event=reply_to_30311_event,
        reply_to_30311_a_tag=reply_to_30311_a_tag,
        reply_relay=effective_reply_relay,
    )


async def _load_template_overrides(user_id: Optional[str]) -> dict[str, dict[str, Any]]:
    """Fetch message templates from DB and assemble into a mapping suitable
    for passing into `build_message(..., template_overrides=...)`.

    Returns a mapping: { category: { key: content_or_dict, ... }, ... }
    User-specific templates (when user_id provided) override global (user_id=None).
    """
    from . import crud

    try:
        # Global templates first
        global_rows = await crud.get_message_templates(None, None)
        user_rows: list[Any] = []
        if user_id:
            user_rows = await crud.get_message_templates(user_id, None)

        combined: dict[str, dict[str, Any]] = {}

        def _assign(row):
            cat = row.category or ""
            combined.setdefault(cat, {})
            raw = getattr(row, "content", "")
            parsed: Any = raw
            if isinstance(raw, str):
                s = raw.strip()
                # Try JSON
                try:
                    parsed_json = json.loads(s)
                    if isinstance(parsed_json, dict):
                        parsed = parsed_json
                    else:
                        parsed = s
                except Exception:
                    try:
                        parsed_eval = ast.literal_eval(s)
                        if isinstance(parsed_eval, dict):
                            parsed = parsed_eval
                        else:
                            parsed = s
                    except Exception:
                        parsed = s
            combined[cat][row.key] = parsed

        for r in global_rows:
            _assign(r)
        for r in user_rows:
            # user overrides take precedence
            _assign(r)

        return combined
    except Exception:
        return {}


async def build_message_bundle(
    event_type: str,
    *,
    new_amount: float = 0,
    difference: float = 0,
    cyber_herd_item: Optional[dict[str, Any]] = None,
    spots_remaining: int = 0,
    relays: Optional[list[str]] = None,
    reply_to_30311_event: Optional[str] = None,
    reply_to_30311_a_tag: Optional[str] = None,
    user_id: Optional[str] = None,
) -> MessageBundle:
    """Expose middleware-equivalent message builder for other modules."""
    # Load DB template overrides when a user_id is provided (user-specific + global)
    template_overrides = {}
    try:
        template_overrides = await _load_template_overrides(user_id)
    except Exception:
        template_overrides = {}

    return await _build_message(
        event_type,
        new_amount=new_amount,
        difference=difference,
        cyber_herd_item=cyber_herd_item,
        spots_remaining=spots_remaining,
        relays=relays,
        reply_to_30311_event=reply_to_30311_event,
        reply_to_30311_a_tag=reply_to_30311_a_tag,
        template_overrides=template_overrides,
    )


# Explicitly export public API
__all__ = [
    "send_to_websocket_clients",
    "is_nostr_publishing_enabled",
    "publish_note",
    "try_publish_note",
    "render_and_publish_template",
    "create_and_sign_event",
    "build_message_bundle",
]
