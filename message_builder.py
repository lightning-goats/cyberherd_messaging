from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from bech32 import bech32_encode, convertbits  # reuse shared dependency

from .defaults import (
    CYBER_HERD_JOIN,
    CYBER_HERD_TREATS,
    DAILY_RESET,
    FEEDER_TRIGGER,
    FEEDING_BONUS,
    FEEDING_FALLBACK,
    FEEDING_REGULAR,
    FEEDING_REMAINDER,
    GOAT_NAMES_DICT,
    HEADBUTT_FAILURE,
    HEADBUTT_INFO,
    HEADBUTT_SUCCESS,
    MEMBER_INCREASE,
    SATS_RECEIVED,
    THANK_YOU_VARIATIONS,
    VARIATIONS,
)
from .utils import get_random_goat_names, join_with_and
from lnbits.utils.nostr import hex_to_npub
from .templates import messaging_templates as TEMPLATES


@dataclass(slots=True)
class MessageBundle:
    """Container holding rendered note/websocket content and metadata."""

    nostr_content: str
    websocket_content: str
    spots_info: str = ""
    goat_data: Optional[List[Dict[str, str]]] = None
    spots_remaining: int = 0
    headbutt_text: str = ""


def format_nostr_event_reference(event_id: Optional[str]) -> Optional[str]:
    """Convert 32-byte hex event id into nostr:note reference."""
    if not event_id or not isinstance(event_id, str):
        return None
    candidate = event_id.strip().lower()
    if len(candidate) != 64:
        return None
    try:
        raw = bytes.fromhex(candidate)
    except ValueError:
        return None
    data = convertbits(raw, 8, 5, True)
    if not data:
        return None
    return bech32_encode("note", data)


def format_nostr_pubkey(pubkey: Optional[str]) -> Optional[str]:
    """Convert 32-byte hex pubkey into npub reference."""
    if not pubkey or not isinstance(pubkey, str):
        return None
    candidate = pubkey.strip().lower()
    if len(candidate) != 64:
        return None
    try:
        return hex_to_npub(candidate)
    except Exception:
        return None


def _pick_template(pool: Dict[str, Any]) -> Any:
    try:
        return random.choice(list(pool.values()))
    except Exception:
        return next(iter(pool.values()))


def _normalize_nprofile(value: Optional[str]) -> Optional[str]:
    if value and isinstance(value, str) and not value.startswith("nostr:"):
        return f"nostr:{value}"
    return value


def _strip_promotional_link(content: str, *, is_30311_reply: bool) -> str:
    if is_30311_reply:
        return content.replace("\n\n https://lightning-goats.com\n\n", "")
    return content


def _format_thanks(amount: int | float, template_overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
    if not amount:
        return ""
    # prefer overrides when provided
    if template_overrides:
        pool = template_overrides.get("thank_you_variations") or template_overrides.get("thank_you_variation")
        if pool:
            template = _pick_template(pool)
        else:
            template = _pick_template(THANK_YOU_VARIATIONS)
    else:
        template = _pick_template(THANK_YOU_VARIATIONS)
    raw = template.get("content") if isinstance(template, dict) else template
    text = str(raw or "")
    if not text:
        return ""
    try:
        return text.format(new_amount=amount)
    except Exception:
        return text


def _format_variation(difference: int | float, template_overrides: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
    # prefer overrides when provided
    if template_overrides:
        pool = template_overrides.get("variations")
        if pool:
            template = _pick_template(pool)
        else:
            template = _pick_template(VARIATIONS)
    else:
        template = _pick_template(VARIATIONS)

    try:
        return template.format(difference=difference)
    except Exception:
        return template


def _select_goats() -> tuple[List[Dict[str, str]], str, str, str]:
    goats = get_random_goat_names(GOAT_NAMES_DICT)
    names = [str(name) for name, *_ in goats]

    normalized_profiles: List[str] = []
    mentions: List[str] = []

    for name, profile, pubkey in goats:
        # Build a Nostr-friendly identifier that includes both an nprofile
        # (if provided) and a p-tag (the raw pubkey hex) when available.
        # Preferred order: use an explicit nprofile when present, otherwise
        # derive an npub from the stored pubkey. If a pubkey exists, append
        # a "p-tag <hex>" fragment so clients can easily extract the raw
        # pubkey for p-tagging.
        identifier = _normalize_nprofile(profile)
        pub_hex = pubkey or None
        npub_from_pubkey = format_nostr_pubkey(pub_hex) if pub_hex else None

        if identifier:
            # identifier is already normalized (starts with 'nostr:')
            identifier_str = str(identifier)
            if pub_hex:
                identifier_str = f"{identifier_str} p-tag {pub_hex}"
        elif npub_from_pubkey:
            identifier_str = f"nostr:{npub_from_pubkey} p-tag {pub_hex}"
        else:
            identifier_str = str(name)
        normalized_profiles.append(identifier_str)
        mentions.append(identifier_str)

    goat_data = [{"name": name, "imageUrl": f"images/{name.lower()}.png"} for name in names]
    goat_names_joined = join_with_and(names)
    goat_profiles_joined = join_with_and(normalized_profiles)
    goat_mentions_joined = join_with_and(mentions)

    return goat_data, goat_names_joined, goat_profiles_joined, goat_mentions_joined


def _safe_template_content(template: Any) -> str:
    if isinstance(template, dict):
        return template.get("content", "")
    return str(template)


def _format_template(template: Any, **kwargs: Any) -> str:
    base = _safe_template_content(template)
    try:
        return base.format(**kwargs)
    except Exception:
        return base


def _build_spots_and_headbutt_info(
    spots_remaining: int,
    ch_item: Dict[str, Any],
    pool_func: Any,
) -> tuple[str, str]:
    """Build spots_info and headbutt_text strings based on remaining spots.
    
    Args:
        spots_remaining: Number of spots available in the herd
        ch_item: Cyber herd item dictionary that may contain headbutt_info
        pool_func: Function to get template pool (typically _pool from build_message)
    
    Returns:
        Tuple of (spots_info, headbutt_text)
    """
    spots_info = ""
    if spots_remaining > 1:
        spots_info = f"⚡ {spots_remaining} more spots available. ⚡"
    elif spots_remaining == 1:
        spots_info = "⚡ 1 more spot available. ⚡"

    headbutt_text = ""
    if not spots_remaining and ch_item.get("headbutt_info"):
        info = ch_item["headbutt_info"]
        head_tpl = _pick_template(pool_func("headbutt_info", HEADBUTT_INFO))
        headbutt_text = " " + _format_template(
            head_tpl,
            required_sats=info.get("required_sats", 10),
            victim_name=info.get("victim_name", "Anon"),
        )
    
    return spots_info, headbutt_text


async def build_message(
    event_type: str,
    *,
    new_amount: float = 0,
    difference: float = 0,
    cyber_herd_item: Optional[Dict[str, Any]] = None,
    spots_remaining: int = 0,
    relays: Optional[List[str]] = None,  # parity argument, unused but kept for compatibility
    reply_to_30311_event: Optional[str] = None,
    reply_to_30311_a_tag: Optional[str] = None,
    template_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
) -> MessageBundle:
    """
    Build nostr and websocket message content mirroring middleware/messaging.py behaviour.
    """

    ch_item = cyber_herd_item or {}
    is_30311_reply = bool(reply_to_30311_event and reply_to_30311_a_tag)

    def _pool(name: str, default: Any) -> Any:
        """Return a template pool, preferring template_overrides when present.

        The function accepts a friendly name (e.g. 'cyber_herd_join') and will
        try a few key variants when looking up overrides so DB categories like
        'sats_received_dict' or 'daily_reset_dict' are matched.
        """
        if not template_overrides:
            return default

        candidates = [
            name,
            name.lower(),
            f"{name.lower()}_dict",
            f"{name.lower().replace('_dict','')}",
        ]
        for key in candidates:
            if key in template_overrides and template_overrides[key]:
                return template_overrides[key]

        # fallback to default pool
        return default

    if event_type in {"cyber_herd", "new_member"}:
        template = _pick_template(_pool("cyber_herd_join", CYBER_HERD_JOIN))
        display_name = ch_item.get("display_name", "anon")
        event_id = ch_item.get("event_id", "")
        pub_key = ch_item.get("pubkey", "")
        nprofile = _normalize_nprofile(ch_item.get("nprofile"))
        amount = ch_item.get("amount", 0)
        thank_you = _format_thanks(amount, template_overrides=template_overrides)
        nostr_name = (
            format_nostr_pubkey(pub_key)
            or nprofile
            or format_nostr_event_reference(event_id)
            or display_name
        )

        spots_info, headbutt_text = _build_spots_and_headbutt_info(spots_remaining, ch_item, _pool)

        nostr_content = _format_template(
            template,
            thanks_part=thank_you,
            name=nostr_name,
            difference=difference,
            new_amount=amount,
            event_id=event_id,
        )
        nostr_content = _strip_promotional_link(
            nostr_content + spots_info + headbutt_text,
            is_30311_reply=is_30311_reply,
        )

        websocket_content = _format_template(
            template,
            thanks_part=thank_you,
            name=display_name,
            difference=difference,
            new_amount=amount,
            event_id=event_id,
        ) + spots_info + headbutt_text

        return MessageBundle(
            nostr_content=nostr_content,
            websocket_content=websocket_content,
            spots_info=spots_info,
            goat_data=None,
            spots_remaining=spots_remaining,
            headbutt_text=headbutt_text,
        )

    if event_type in {"feeder_triggered", "feeder_trigger_bolt12", "sats_received"}:
        bolt_prefix = "⚡BOLT12 PAYMENT⚡ " if event_type == "feeder_trigger_bolt12" else ""
        template_pool = (
            _pool("sats_received", SATS_RECEIVED) if event_type == "sats_received" else _pool("feeder_trigger", FEEDER_TRIGGER)
        )
        template = _pick_template(template_pool)
        content = _safe_template_content(template)

        difference_message = _format_variation(difference, template_overrides=template_overrides)
        goat_data = None
        goat_names = ""
        goat_profiles = ""
        goat_mentions = ""

        if "{goat_name}" in content:
            goat_data, goat_names, goat_profiles, goat_mentions = _select_goats()

        nostr_body = content.format(
            new_amount=new_amount,
            goat_name=goat_mentions or goat_profiles,
            difference_message=difference_message,
        )
        websocket_body = content.format(
            new_amount=new_amount,
            goat_name=goat_names,
            difference_message=difference_message,
        )

        nostr_content = _strip_promotional_link(bolt_prefix + nostr_body, is_30311_reply=is_30311_reply)
        websocket_content = bolt_prefix + websocket_body if bolt_prefix else websocket_body

        return MessageBundle(
            nostr_content=nostr_content,
            websocket_content=websocket_content,
            goat_data=goat_data,
        )

    if event_type == "headbutt_info":
        template = _pick_template(_pool("headbutt_info", HEADBUTT_INFO))
        required_sats = ch_item.get("required_sats", 0)
        victim_name = ch_item.get("victim_name", "Anon")
        victim_pubkey = ch_item.get("victim_pubkey", "")
        victim_nprofile = _normalize_nprofile(ch_item.get("victim_nprofile"))
        victim_display = ch_item.get("victim_display_name", victim_name)
        victim_nostr = format_nostr_pubkey(victim_pubkey) or victim_nprofile or victim_display

        nostr_content = _format_template(
            template, required_sats=required_sats, victim_name=victim_nostr
        )
        nostr_content = _strip_promotional_link(nostr_content, is_30311_reply=is_30311_reply)

        websocket_content = _format_template(
            template, required_sats=required_sats, victim_name=victim_display
        )
        return MessageBundle(nostr_content=nostr_content, websocket_content=websocket_content)

    if event_type == "headbutt_success":
        template = _pick_template(_pool("headbutt_success", HEADBUTT_SUCCESS))
        attacker_name = ch_item.get("attacker_name", "Anon")
        attacker_amount = ch_item.get("attacker_amount", 0)
        victim_name = ch_item.get("victim_name", "Anon")
        victim_amount = ch_item.get("victim_amount", 0)
        attacker_pubkey = ch_item.get("attacker_pubkey", "")
        victim_pubkey = ch_item.get("victim_pubkey", "")
        attacker_nprofile = _normalize_nprofile(ch_item.get("attacker_nprofile"))
        victim_nprofile = _normalize_nprofile(ch_item.get("victim_nprofile"))

        nostr_attacker = (
            format_nostr_pubkey(attacker_pubkey)
            or attacker_nprofile
            or format_nostr_event_reference(ch_item.get("event_id"))
            or attacker_name
        )
        nostr_victim = format_nostr_pubkey(victim_pubkey) or victim_nprofile or victim_name

        base_note = _format_template(
            template,
            attacker_name=nostr_attacker,
            attacker_amount=attacker_amount,
            victim_name=nostr_victim,
            victim_amount=victim_amount,
        )
        attacker_display_name = ch_item.get("attacker_display_name", attacker_name)
        victim_display_name = ch_item.get("victim_display_name", victim_name)
        base_client = _format_template(
            template,
            attacker_name=attacker_display_name,
            attacker_amount=attacker_amount,
            victim_name=victim_display_name,
            victim_amount=victim_amount,
        )

        headbutt_text = ""
        if ch_item.get("next_headbutt_info"):
            info = ch_item["next_headbutt_info"]
            next_tpl = _pick_template(_pool("headbutt_info", HEADBUTT_INFO))
            headbutt_text = " " + _format_template(
                next_tpl,
                required_sats=info.get("required_sats", 10),
                victim_name=info.get("victim_name", "Anon"),
            )

        nostr_content = _strip_promotional_link(base_note + headbutt_text, is_30311_reply=is_30311_reply)
        websocket_content = base_client + headbutt_text
        return MessageBundle(
            nostr_content=nostr_content,
            websocket_content=websocket_content,
            headbutt_text=headbutt_text,
        )

    if event_type == "headbutt_failure":
        template = _pick_template(_pool("headbutt_failure", HEADBUTT_FAILURE))
        attacker_name = ch_item.get("attacker_name", "Anon")
        attacker_amount = ch_item.get("attacker_amount", 0)
        victim_name = ch_item.get("victim_name", "Anon")
        victim_amount = ch_item.get("victim_amount", 0)
        required_amount = ch_item.get("required_amount", 0)
        attacker_pubkey = ch_item.get("attacker_pubkey", "")
        victim_pubkey = ch_item.get("victim_pubkey", "")
        attacker_nprofile = _normalize_nprofile(ch_item.get("attacker_nprofile"))
        victim_nprofile = _normalize_nprofile(ch_item.get("victim_nprofile"))

        nostr_attacker = format_nostr_pubkey(attacker_pubkey) or attacker_nprofile or attacker_name
        nostr_victim = format_nostr_pubkey(victim_pubkey) or victim_nprofile or victim_name

        nostr_content = _format_template(
            template,
            attacker_name=nostr_attacker,
            attacker_amount=attacker_amount,
            victim_name=nostr_victim,
            victim_amount=victim_amount,
            required_amount=required_amount,
        )
        nostr_content = _strip_promotional_link(nostr_content, is_30311_reply=is_30311_reply)

        attacker_display_name = ch_item.get("attacker_display_name", attacker_name)
        victim_display_name = ch_item.get("victim_display_name", victim_name)
        websocket_content = _format_template(
            template,
            attacker_name=attacker_display_name,
            attacker_amount=attacker_amount,
            victim_name=victim_display_name,
            victim_amount=victim_amount,
            required_amount=required_amount,
        )
        return MessageBundle(nostr_content=nostr_content, websocket_content=websocket_content)

    if event_type == "cyber_herd_treats":
        template = _pick_template(_pool("cyber_herd_treats", CYBER_HERD_TREATS))
        display_name = ch_item.get("display_name", "Anon")
        amount = ch_item.get("amount", 0)
        pub_key = ch_item.get("pubkey")
        nprofile = _normalize_nprofile(ch_item.get("nprofile"))
        nostr_name = format_nostr_pubkey(pub_key) or nprofile or display_name

        nostr_content = _format_template(template, name=nostr_name, new_amount=amount)
        websocket_content = _format_template(template, name=display_name, new_amount=amount)
        return MessageBundle(nostr_content=nostr_content, websocket_content=websocket_content)

    if event_type == "member_increase":
        template = _pick_template(_pool("member_increase", MEMBER_INCREASE))
        display_name = ch_item.get("display_name", "Anon")
        pub_key = ch_item.get("pubkey", "")
        nprofile = _normalize_nprofile(ch_item.get("nprofile"))
        amount = ch_item.get("amount", 0)
        increase_amount = ch_item.get("new_zap_amount", 0)
        nostr_name = format_nostr_pubkey(pub_key) or nprofile or display_name

        spots_info, headbutt_text = _build_spots_and_headbutt_info(spots_remaining, ch_item, _pool)

        nostr_content = _format_template(
            template,
            member_name=nostr_name,
            increase_amount=increase_amount,
            new_total=amount,
        )
        nostr_content = _strip_promotional_link(
            nostr_content + spots_info + headbutt_text,
            is_30311_reply=is_30311_reply,
        )

        websocket_content = _format_template(
            template,
            member_name=display_name,
            increase_amount=increase_amount,
            new_total=amount,
        ) + spots_info + headbutt_text

        return MessageBundle(
            nostr_content=nostr_content,
            websocket_content=websocket_content,
            spots_info=spots_info,
            spots_remaining=spots_remaining,
            headbutt_text=headbutt_text,
        )

    if event_type == "daily_reset":
        template = _pick_template(_pool("daily_reset", DAILY_RESET))
        content = _format_template(template)
        return MessageBundle(nostr_content=content, websocket_content=content)

    elif event_type in {
        "herd_reset_message",
        "interface_info",
        "kind_6_headbutt_failure",
        "kind_6_repost",
        "kind_7_headbutt_failure",
        "kind_7_reaction",
        "sats_received_zap",
        "zapper_displaces_kind_6",
        "zapper_displaces_kind_7",
    }:
        # Implement specialised event rendering using the templates module.
        # Herd reset mirrors the daily reset template.
        if event_type == "herd_reset_message":
            template = _pick_template(DAILY_RESET)
            content = _format_template(template)
            return MessageBundle(nostr_content=content, websocket_content=content)

        # Interface information (status/help text)
        if event_type == "interface_info":
            tpl_pool = getattr(TEMPLATES, "interface_info", None)
            if tpl_pool is None:
                logger.warning("message_builder: interface_info templates missing")
                fallback = json.dumps({"event": event_type, "payload": ch_item}, ensure_ascii=False)
                return MessageBundle(nostr_content=fallback, websocket_content=fallback)

            template = _pick_template(tpl_pool)
            nostr_content = _format_template(template)
            nostr_content = _strip_promotional_link(nostr_content, is_30311_reply=is_30311_reply)
            websocket_content = _format_template(template)
            return MessageBundle(nostr_content=nostr_content, websocket_content=websocket_content)

        # Repost / reaction joins (kind_6_repost, kind_7_reaction)
        if event_type in {"kind_6_repost", "kind_7_reaction"}:
            pool_name = "kind_6_repost" if event_type == "kind_6_repost" else "kind_7_reaction"
            tpl_pool = getattr(TEMPLATES, pool_name, None)
            if tpl_pool is None:
                logger.warning("message_builder: %s templates missing", pool_name)
                fallback = json.dumps({"event": event_type, "payload": ch_item}, ensure_ascii=False)
                return MessageBundle(nostr_content=fallback, websocket_content=fallback)

            template = _pick_template(tpl_pool)
            display_name = ch_item.get("display_name", "Anon")
            pub_key = ch_item.get("pubkey", "")
            nprofile = _normalize_nprofile(ch_item.get("nprofile"))
            nostr_name = format_nostr_pubkey(pub_key) or nprofile or display_name

            spots_info, headbutt_text = _build_spots_and_headbutt_info(spots_remaining, ch_item, _pool)

            nostr_content = _format_template(template, name=nostr_name)
            nostr_content = _strip_promotional_link(
                nostr_content + spots_info + headbutt_text,
                is_30311_reply=is_30311_reply,
            )

            websocket_content = _format_template(template, name=display_name) + spots_info + headbutt_text

            return MessageBundle(
                nostr_content=nostr_content,
                websocket_content=websocket_content,
                spots_info=spots_info,
                spots_remaining=spots_remaining,
                headbutt_text=headbutt_text,
            )

        # Headbutt failure for reposts/reactions (specialised messages)
        if event_type in {"kind_6_headbutt_failure", "kind_7_headbutt_failure"}:
            pool_name = "kind_6_headbutt_failure" if event_type == "kind_6_headbutt_failure" else "kind_7_headbutt_failure"
            tpl_pool = getattr(TEMPLATES, pool_name, None)
            if tpl_pool is None:
                logger.warning("message_builder: %s templates missing", pool_name)
                fallback = json.dumps({"event": event_type, "payload": ch_item}, ensure_ascii=False)
                return MessageBundle(nostr_content=fallback, websocket_content=fallback)

            template = _pick_template(tpl_pool)
            display_name = ch_item.get("display_name", "Anon")
            pub_key = ch_item.get("pubkey", "")
            nprofile = _normalize_nprofile(ch_item.get("nprofile"))
            nostr_name = format_nostr_pubkey(pub_key) or nprofile or display_name

            required_sats = ch_item.get("required_sats", ch_item.get("required_amount", 0))
            victim_display = ch_item.get("victim_display_name", ch_item.get("victim_name", "Anon"))
            victim_pubkey = ch_item.get("victim_pubkey", "")
            victim_nprofile = _normalize_nprofile(ch_item.get("victim_nprofile"))
            nostr_victim = format_nostr_pubkey(victim_pubkey) or victim_nprofile or victim_display

            nostr_content = _format_template(
                template, name=nostr_name, required_sats=required_sats, victim_name=nostr_victim
            )
            nostr_content = _strip_promotional_link(nostr_content, is_30311_reply=is_30311_reply)

            websocket_content = _format_template(
                template, name=display_name, required_sats=required_sats, victim_name=victim_display
            )
            return MessageBundle(nostr_content=nostr_content, websocket_content=websocket_content)

        # sats_received_zap: reuse sats received templates but mark as zap event
        if event_type == "sats_received_zap":
            template_pool = SATS_RECEIVED
            template = _pick_template(template_pool)
            content = _safe_template_content(template)

            difference_message = _format_variation(difference, template_overrides=template_overrides)
            goat_data = None
            goat_names = ""
            goat_profiles = ""
            goat_mentions = ""

            if "{goat_name}" in content:
                goat_data, goat_names, goat_profiles, goat_mentions = _select_goats()

            nostr_body = content.format(
                new_amount=new_amount,
                goat_name=goat_mentions or goat_profiles,
                difference_message=difference_message,
            )
            websocket_body = content.format(
                new_amount=new_amount,
                goat_name=goat_names,
                difference_message=difference_message,
            )

            nostr_content = _strip_promotional_link(nostr_body, is_30311_reply=is_30311_reply)
            websocket_content = websocket_body

            return MessageBundle(nostr_content=nostr_content, websocket_content=websocket_content, goat_data=goat_data)

        # Zapper displaces repost/reaction (paid zap displaces non-paid entries)
        if event_type in {"zapper_displaces_kind_6", "zapper_displaces_kind_7"}:
            pool_name = "zapper_displaces_kind_6" if event_type == "zapper_displaces_kind_6" else "zapper_displaces_kind_7"
            tpl_pool = getattr(TEMPLATES, pool_name, None)
            if tpl_pool is None:
                logger.warning("message_builder: %s templates missing", pool_name)
                fallback = json.dumps({"event": event_type, "payload": ch_item}, ensure_ascii=False)
                return MessageBundle(nostr_content=fallback, websocket_content=fallback)

            template = _pick_template(tpl_pool)

            attacker_name = ch_item.get("attacker_display_name", ch_item.get("attacker_name", "Anon"))
            attacker_pubkey = ch_item.get("attacker_pubkey", "")
            attacker_nprofile = _normalize_nprofile(ch_item.get("attacker_nprofile"))
            nostr_attacker = format_nostr_pubkey(attacker_pubkey) or attacker_nprofile or attacker_name

            victim_name = ch_item.get("victim_display_name", ch_item.get("victim_name", "Anon"))
            victim_pubkey = ch_item.get("victim_pubkey", "")
            victim_nprofile = _normalize_nprofile(ch_item.get("victim_nprofile"))
            nostr_victim = format_nostr_pubkey(victim_pubkey) or victim_nprofile or victim_name

            attacker_amount = ch_item.get("attacker_amount", 0)

            spots_info, headbutt_text = _build_spots_and_headbutt_info(spots_remaining, ch_item, _pool)

            nostr_content = _format_template(
                template,
                attacker_name=nostr_attacker,
                attacker_amount=attacker_amount,
                victim_name=nostr_victim,
            )
            nostr_content = _strip_promotional_link(
                nostr_content + spots_info + headbutt_text,
                is_30311_reply=is_30311_reply,
            )

            websocket_content = _format_template(
                template,
                attacker_name=attacker_name,
                attacker_amount=attacker_amount,
                victim_name=victim_name,
            ) + spots_info + headbutt_text

            return MessageBundle(
                nostr_content=nostr_content,
                websocket_content=websocket_content,
                spots_info=spots_info,
                spots_remaining=spots_remaining,
                headbutt_text=headbutt_text,
            )

        # Last resort fallback for unexpected missing templates
        logger.warning("message_builder: event type %s is not fully implemented yet.", event_type)
        fallback_content = json.dumps({"event": event_type, "payload": ch_item}, ensure_ascii=False)
        return MessageBundle(nostr_content=fallback_content, websocket_content=fallback_content)

    if event_type in {"feeding_regular", "feeding_bonus", "feeding_remainder", "feeding_fallback"}:
        pools = {
            "feeding_regular": FEEDING_REGULAR,
            "feeding_bonus": FEEDING_BONUS,
            "feeding_remainder": FEEDING_REMAINDER,
            "feeding_fallback": FEEDING_FALLBACK,
        }
        template = _pick_template(pools[event_type])
        display_name = ch_item.get("display_name", "member")
        amount = int(new_amount) if new_amount else 0
        content = _format_template(
            template,
            new_amount=amount,
            display_name=display_name,
            name=display_name,
        )
        return MessageBundle(nostr_content=content, websocket_content=content)

    # Fallback: log and return JSON payload so callers can detect unsupported events.
    fallback = json.dumps({"event": event_type, "payload": ch_item}, ensure_ascii=False)
    logger.warning("message_builder: falling back to JSON payload for event %s", event_type)
    return MessageBundle(nostr_content=fallback, websocket_content=fallback)
