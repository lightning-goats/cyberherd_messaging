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

_nostrclient_check_lock: Optional[asyncio.Lock] = None
_nostrclient_available: Optional[bool] = None


def _get_nostrclient_check_lock() -> asyncio.Lock:
    """Lazy-init the nostrclient check lock to avoid binding to import-time event loop."""
    global _nostrclient_check_lock
    if _nostrclient_check_lock is None:
        _nostrclient_check_lock = asyncio.Lock()
    return _nostrclient_check_lock


class _SafeFormatter(string.Formatter):
    """Formatter that only allows simple variable substitution.

    Blocks attribute access (e.g. ``{foo.__class__}``), item access
    (e.g. ``{foo[0]}``), and other traversal patterns that could leak
    internals via ``str.format(**user_dict)``.
    """

    def get_field(self, field_name, args, kwargs):
        if not isinstance(field_name, str) or not field_name.isidentifier():
            raise ValueError(
                f"Only simple variable names allowed in templates, got: {field_name!r}"
            )
        try:
            return kwargs[field_name], field_name
        except KeyError:
            # Leave unresolved placeholders intact
            return f"{{{field_name}}}", field_name


_safe_fmt = _SafeFormatter()


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

    async with _get_nostrclient_check_lock():
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


async def _try_bunker_sign_and_publish(
    wallet_id: str | None,
    content: str,
    kind: int,
    tags: list[list[str]],
) -> bool:
    """Sign an event via nsecbunker and publish to relays.

    Returns True on success, False if bunker is unavailable, has no key,
    lacks permission, or is rate-limited.
    """
    if not wallet_id:
        return False

    try:
        from lnbits.extensions.nsecbunker.services import sign_event
    except ImportError:
        logger.debug("cyberherd_messaging: nsecbunker not installed, skipping bunker signing")
        return False

    try:
        signed = await sign_event(
            wallet_id,
            "cyberherd_messaging",
            {"kind": kind, "tags": tags, "content": content},
        )
    except LookupError as exc:
        logger.info("cyberherd_messaging: bunker LookupError for wallet {}: {}", wallet_id[:12], exc)
        return False
    except PermissionError as exc:
        logger.info("cyberherd_messaging: bunker PermissionError: {}", exc)
        return False
    except Exception as exc:
        logger.warning("cyberherd_messaging: bunker sign_event error ({}): {}", type(exc).__name__, exc)
        return False

    # Publish the signed event dict via nostrclient relay_manager
    try:
        from lnbits.extensions.nostrclient.router import nostr_client

        if not hasattr(nostr_client, "relay_manager"):
            logger.warning("cyberherd_messaging: nostr_client has no relay_manager (bunker path)")
            return False

        wire_msg = json.dumps(["EVENT", signed])
        nostr_client.relay_manager.publish_message(wire_msg)

        event_id = signed.get("id", "")[:8]
        logger.info(
            "cyberherd_messaging: published kind {} event {}... via bunker to {} relays",
            kind,
            event_id,
            len(nostr_client.relay_manager.relays),
        )
        return True
    except Exception as exc:
        logger.error("cyberherd_messaging: bunker publish failed: {}", exc)
        return False


async def get_bunker_pubkey(wallet_id: str | None) -> str | None:
    """Return the bunker public key hex for a wallet, or None."""
    if not wallet_id:
        return None
    try:
        from lnbits.extensions.nsecbunker.services import get_wallet_pubkey

        return await get_wallet_pubkey(wallet_id)
    except ImportError:
        return None
    except Exception:
        return None


async def check_bunker_status(wallet_id: str | None) -> dict:
    """Check nsecbunker availability and configuration for a wallet.

    Returns a dict with keys: installed, has_key, pubkey, has_permissions.
    """
    result = {"installed": False, "has_key": False, "pubkey": None, "has_permissions": False}
    if not wallet_id:
        return result

    try:
        from lnbits.extensions.nsecbunker.services import get_wallet_pubkey
    except ImportError:
        return result

    result["installed"] = True

    try:
        pubkey = await get_wallet_pubkey(wallet_id)
    except Exception:
        pubkey = None

    if pubkey:
        result["has_key"] = True
        result["pubkey"] = pubkey
    else:
        return result

    # Check permissions for cyberherd_messaging (kind 1 and kind 1311)
    try:
        from lnbits.extensions.nsecbunker.crud import get_permission_for_signing

        perm_1 = await get_permission_for_signing(wallet_id, "cyberherd_messaging", 1)
        perm_1311 = await get_permission_for_signing(wallet_id, "cyberherd_messaging", 1311)
        result["has_permissions"] = bool(perm_1 or perm_1311)
    except Exception:
        result["has_permissions"] = False

    return result


async def find_bunker_wallet(user_id: str) -> str | None:
    """Return the first wallet_id for *user_id* that has an nsecbunker key.

    Returns None if nsecbunker is not installed or no wallet has a key.
    """
    try:
        from lnbits.core.crud import get_wallets
        from lnbits.extensions.nsecbunker.services import get_wallet_pubkey
    except ImportError:
        return None

    try:
        wallets = await get_wallets(user_id)
    except Exception:
        return None

    for w in wallets:
        try:
            pubkey = await get_wallet_pubkey(w.id)
            if pubkey:
                return w.id
        except Exception:
            continue
    return None


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
                logger.info("cyberherd_messaging: nostr publishing disabled by setting (nostr_publishing_enabled={})", normalized)
                return False
            
            logger.debug("cyberherd_messaging: nostr publishing enabled by setting (nostr_publishing_enabled={})", normalized)
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


async def publish_note(
    content: str,
    *,
    tags: list[tuple[str, str]] | None = None,
    e_tags: list[str] | None = None,
    p_tags: list[str] | None = None,
    reply_to_30311_event: str | None = None,
    reply_to_30311_a_tag: str | None = None,
    reply_relay: str | None = None,
    wallet_id: str,
) -> bool:
    """Publish a nostr note via nsecbunker signing only.

    - Signs the event via nsecbunker using the provided wallet_id.
    - Supports e_tags (reply threading), p_tags (mentions), and arbitrary tags.
    - Returns False if bunker signing fails (no local-key fallback).
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

    # --- Sign via nsecbunker and publish ---
    formatted_tags = []
    for tag in all_tags:
        if isinstance(tag, (list, tuple)):
            formatted_tags.append([str(part) for part in tag])
        else:
            formatted_tags.append([str(tag)])

    # Determine kind from tags
    has_30311_tags = any(
        len(tag) >= 2 and tag[0] == "a" and str(tag[1]).startswith("30311:")
        for tag in formatted_tags
    )
    kind = 1311 if has_30311_tags else 1

    bunker_ok = await _try_bunker_sign_and_publish(
        wallet_id, content, kind, formatted_tags
    )
    if bunker_ok:
        return True

    logger.warning(
        "cyberherd_messaging: bunker signing failed for wallet {}, no fallback available",
        wallet_id[:12] if wallet_id else "?",
    )
    return False


async def try_publish_note(
    content: str,
    *,
    e_tags: list[str] | None = None,
    p_tags: list[str] | None = None,
    reply_relay: str | None = None,
    wallet_id: str,
) -> bool:
    """Convenience wrapper around publish_note."""
    logger.info(
        f"cyberherd_messaging: try_publish_note content_len={len(content or '')} "
        f"e_tags={e_tags} p_tags={p_tags} wallet_id={wallet_id[:12] if wallet_id else '?'}"
    )

    return await publish_note(
        content,
        e_tags=e_tags,
        p_tags=p_tags,
        reply_relay=reply_relay,
        wallet_id=wallet_id,
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

        # Note: don't use values.get("name") as fallback since "name" is often the nostr-formatted
        # name (npub/nprofile) intended for nostr messages, not the human-readable display name
        display_name = (
            values.get("member_display_name")
            or values.get("display_name")
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
        logger.debug("cyberherd_messaging: failed to augment membership message: {}", exc)
        return base_content, None


async def render_and_publish_template(
    *,
    user_id: str,
    category: str,
    key: str,
    values: dict[str, Any] | None = None,
    e_tags: list[str] | None = None,
    p_tags: list[str] | None = None,
    reply_to_30311_event: str | None = None,
    reply_to_30311_a_tag: str | None = None,
    reply_relay: str | None = None,
    return_websocket_message: bool = False,
    wallet_id: str,
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

    # For websocket messages, substitute {name} with display name instead of nprofile
    if return_websocket_message and isinstance(values, dict):
        # Get display_name from various possible sources
        display_name_for_ws = (
            values.get("member_display_name")
            or values.get("display_name")
            or (values.get("cyber_herd_item", {}) or {}).get("display_name")
        )
        # Only substitute if we have a display name and the current name looks like an nprofile
        if display_name_for_ws:
            current_name = values.get("name", "")
            if isinstance(current_name, str) and ("nostr:" in current_name or current_name.startswith("nprofile")):
                values = dict(values)
                values["name"] = display_name_for_ws

    # Render the template
    try:
        rendered_content = _safe_fmt.format(str(template_str), **values)
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
        # Use websocket_content from bundle if available (contains display names instead of nprofiles)
        ws_content = rendered_content
        if augmented_bundle and augmented_bundle.websocket_content:
            ws_content = augmented_bundle.websocket_content
        return (ws_content, goat_data)
    
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
        reply_to_30311_event=reply_to_30311_event,
        reply_to_30311_a_tag=reply_to_30311_a_tag,
        reply_relay=effective_reply_relay,
        wallet_id=wallet_id,
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
    "build_message_bundle",
    "check_bunker_status",
    "get_bunker_pubkey",
    "find_bunker_wallet",
]
