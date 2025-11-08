from http import HTTPStatus
from typing import Optional, Dict, Any

import ast
import json
from typing import Tuple
import random

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Security
from pydantic import BaseModel

from lnbits.core.models import User, WalletTypeInfo
from lnbits.decorators import require_admin_key, api_key_header, optional_user_id
from lnbits.core.crud import get_wallet_for_key, get_user_active_extensions_ids

from . import crud, services
from .defaults import SEED_DEFAULTS


class PublishPayload(BaseModel):
    content: str
    e_tags: Optional[list[str]] = None
    p_tags: Optional[list[str]] = None
    reply_relay: Optional[str] = None


class WsBroadcastPayload(BaseModel):
    """Payload for WebSocket broadcast.
    
    Topic is automatically determined from the authenticated wallet's invoice key.
    The category is used for message typing.
    """
    category: str
    message: dict


class MessageTemplatePayload(BaseModel):
    category: str
    key: str
    content: str
    reply_relay: Optional[str] = None


class PublishTemplatePayload(BaseModel):
    category: str
    key: str
    e_tags: Optional[list[str]] = None
    p_tags: Optional[list[str]] = None
    reply_relay: Optional[str] = None


class PublishTemplateWithValuesPayload(BaseModel):
    category: str
    key: str
    values: Optional[Dict[str, Any]] = None
    e_tags: Optional[list[str]] = None
    p_tags: Optional[list[str]] = None
    reply_to_30311_event: Optional[str] = None
    reply_to_30311_a_tag: Optional[str] = None
    reply_relay: Optional[str] = None
    return_websocket_message: bool = False


cyberherd_messaging_api_router = APIRouter()


# ============================================================================
# Extension Access Helper
# ============================================================================

async def check_extension_enabled(user_id: str) -> None:
    """Check if the cyberherd_messaging extension is enabled for the user.
    
    Args:
        user_id: The user ID to check
        
    Raises:
        HTTPException: If extension is not enabled for the user
    """
    active_extensions = await get_user_active_extensions_ids(user_id)
    if "cyberherd_messaging" not in active_extensions:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="CyberHerd Messaging extension is not enabled for this user."
        )


# ============================================================================
# Messaging Endpoints - ALL REQUIRE ADMIN KEY FOR SECURITY
# ============================================================================

@cyberherd_messaging_api_router.post(
    "/api/v1/publish", 
    status_code=HTTPStatus.OK,
    summary="Publish a note to Nostr",
    description="Publishes a note to configured Nostr relays. Requires admin key."
)
async def api_publish_note(
    payload: PublishPayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
) -> dict:
    """Publish a note to Nostr relays.
    
    Security: Requires admin key authentication to prevent unauthorized
    publishing and potential spam attacks.
    """
    # Check if extension is enabled for user
    await check_extension_enabled(wallet_info.wallet.user)
    
    try:
        stored_key = await crud.get_user_setting(wallet_info.wallet.user, "nostr_private_key")
        if not stored_key:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="No stored Nostr private key configured",
            )
        ok = await services.try_publish_note(
            payload.content,
            e_tags=payload.e_tags,
            p_tags=payload.p_tags,
            reply_relay=payload.reply_relay,
            private_key=stored_key,
        )
        if not ok:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, 
                detail="Failed to publish note"
            )
        return {"published": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=str(e)
        ) from e


@cyberherd_messaging_api_router.post(
    "/api/v1/ws_broadcast", 
    status_code=HTTPStatus.OK,
    summary="Broadcast message to WebSocket clients",
    description="Broadcasts a message to WebSocket clients subscribed to this wallet's topic. Topic is automatically determined from the admin key."
)
async def api_ws_broadcast(
    payload: WsBroadcastPayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
) -> dict:
    """Broadcast a message to WebSocket clients.
    
    Security: Requires admin key authentication to prevent:
    - Unauthorized message broadcasting
    - Message spoofing/injection attacks
    - Cross-wallet message injection
    
    The WebSocket topic is automatically determined from the authenticated
    wallet's invoice key, ensuring messages are only sent to the correct
    wallet's subscribers.
    
    Flow:
    1. Admin key (from X-Api-Key header) is validated by require_admin_key
    2. Wallet object is retrieved, containing the invoice key
    3. Invoice key is used as the WebSocket topic
    4. Message is broadcast to all clients subscribed to that topic
    """
    # Check if extension is enabled for user
    await check_extension_enabled(wallet_info.wallet.user)
    
    # Get the invoice key from the authenticated wallet
    # This ensures messages can only be sent to the wallet's own topic
    topic = wallet_info.wallet.inkey
    
    # Broadcast to all clients subscribed to this wallet's invoice key
    ok = await services.send_to_websocket_clients(topic, payload.message)
    
    return {
        "sent": bool(ok),
        "topic": topic,  # Return topic for debugging/verification
        "category": payload.category
    }


@cyberherd_messaging_api_router.post(
    "/api/v1/publish_template", status_code=HTTPStatus.OK
)
async def api_publish_template(
    payload: PublishTemplatePayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
) -> dict:
    # Check if extension is enabled for user
    await check_extension_enabled(wallet_info.wallet.user)
    
    template = await crud.get_message_template(wallet_info.wallet.user, payload.category, payload.key)
    if not template:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Template not found")

    stored_key = await crud.get_user_setting(wallet_info.wallet.user, "nostr_private_key")
    if not stored_key:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="No stored Nostr private key configured",
        )

    try:
        ok = await services.try_publish_note(
            template.content,
            e_tags=payload.e_tags,
            p_tags=payload.p_tags,
            reply_relay=payload.reply_relay,
            private_key=stored_key,
        )
        if not ok:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Failed to publish note")
        return {"published": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)) from e


@cyberherd_messaging_api_router.post(
    "/api/v1/publish_template_with_values", status_code=HTTPStatus.OK
)
async def api_publish_template_with_values(
    payload: PublishTemplateWithValuesPayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
) -> dict:
    # Check if extension is enabled for user
    await check_extension_enabled(wallet_info.wallet.user)
    try:
        stored_key = await crud.get_user_setting(wallet_info.wallet.user, "nostr_private_key")
        if not stored_key and not payload.return_websocket_message:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="No stored Nostr private key configured",
            )
        result = await services.render_and_publish_template(
            user_id=wallet_info.wallet.user,
            category=payload.category,
            key=payload.key,
            values=payload.values,
            e_tags=payload.e_tags,
            p_tags=payload.p_tags,
            reply_relay=payload.reply_relay,
            private_key=stored_key,
            reply_to_30311_event=payload.reply_to_30311_event,
            reply_to_30311_a_tag=payload.reply_to_30311_a_tag,
            return_websocket_message=payload.return_websocket_message,
        )

        if payload.return_websocket_message:
            # When return_websocket_message is True, result is (websocket_message, goat_data)
            if isinstance(result, tuple) and len(result) == 2:
                websocket_message, goat_data = result
                return {
                    "websocket_message": websocket_message,
                    "goat_data": goat_data,
                    "published": False  # Not published to Nostr, just returned for websocket
                }
            else:
                raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Invalid response format")
        else:
            # Normal publishing mode
            if not result:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Failed to publish template")
            return {"published": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)) from e


@cyberherd_messaging_api_router.get("/api/v1/templates")
async def api_get_templates(
    category: Optional[str] = None,
    api_key: Optional[str] = Security(api_key_header),
):
    """Public read endpoint for templates.

    If an admin API key is provided, results are filtered to that user's templates.
    Otherwise, return templates across all users.
    """
    user_id: Optional[str] = None
    if api_key:
        wallet = await get_wallet_for_key(api_key)
        if wallet:
            user_id = wallet.user

    templates = await crud.get_message_templates(user_id, category)
    return {"templates": [t.dict() for t in templates]}


@cyberherd_messaging_api_router.get("/api/v1/templates/categories")
async def api_get_categories(api_key: Optional[str] = Security(api_key_header)):
    """Public read endpoint for template categories.

    If an admin API key is provided, categories are limited to that user's templates.
    """
    user_id: Optional[str] = None
    if api_key:
        wallet = await get_wallet_for_key(api_key)
        if wallet:
            user_id = wallet.user

    templates = await crud.get_message_templates(user_id, None)
    
    # Sort categories numerically if they are numbers, otherwise alphabetically
    def numeric_sort_key(category: str):
        try:
            return (0, float(category))  # Numbers first, sorted numerically
        except ValueError:
            return (1, category)  # Non-numbers second, sorted alphabetically
    
    categories = sorted({t.category for t in templates}, key=numeric_sort_key)
    return {"categories": categories}


@cyberherd_messaging_api_router.get("/api/v1/templates/category/{category}/random")
async def api_get_random_template(
    category: str,
    api_key: Optional[str] = Security(api_key_header)
):
    """Get a random template from a category.
    
    Args:
        category: The template category
        api_key: Optional API key for filtering by user
    
    Returns:
        A randomly selected template from the category
    """
    user_id: Optional[str] = None
    if api_key:
        wallet = await get_wallet_for_key(api_key)
        if wallet:
            user_id = wallet.user
    
    templates = await crud.get_message_templates(user_id, category)
    
    if not templates:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"No templates found in category '{category}'")
    
    template = random.choice(templates)
    return template.dict()


@cyberherd_messaging_api_router.get("/api/v1/templates/{category}/{key}")
async def api_get_template(
    category: str,
    key: str,
    api_key: Optional[str] = Security(api_key_header)
):
    """Get a specific template by category and key.
    
    Args:
        category: The template category
        key: The template key
        api_key: Optional API key for filtering by user
    
    Returns:
        The requested template
    """
    user_id: Optional[str] = None
    if api_key:
        wallet = await get_wallet_for_key(api_key)
        if wallet:
            user_id = wallet.user
    
    if user_id:
        template = await crud.get_message_template(user_id, category, key)
    else:
        # For public access, search through all templates
        templates = await crud.get_message_templates(None, category)
        template = next((t for t in templates if t.key == key), None)
    
    if not template:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Template not found")
    
    return template.dict()


@cyberherd_messaging_api_router.post("/api/v1/templates", status_code=HTTPStatus.CREATED)
async def api_create_template(
    payload: MessageTemplatePayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
):
    await check_extension_enabled(wallet_info.wallet.user)
    # Allow content to be a serialized dict string containing {content, reply_relay}
    def _extract_content_and_reply(raw: str) -> Tuple[str, Optional[str]]:
        if not isinstance(raw, str):
            return (str(raw or ""), None)
        # Try JSON first
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and 'content' in parsed:
                return (parsed.get('content') or '', parsed.get('reply_relay'))
        except Exception:
            pass
        # Fallback to Python literal parsing (single-quoted dicts)
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, dict) and 'content' in parsed:
                return (str(parsed.get('content') or ''), parsed.get('reply_relay'))
        except Exception:
            pass
        return (raw, None)

    tpl_content, tpl_reply = _extract_content_and_reply(payload.content)

    template = await crud.create_message_template(
        wallet_info.wallet.user,
        payload.category,
        payload.key,
        tpl_content,
        payload.reply_relay or tpl_reply,
    )
    return template.dict()


# Category-specific routes must come BEFORE generic {category}/{key} routes
# to avoid FastAPI matching "category" as a path parameter
@cyberherd_messaging_api_router.delete("/api/v1/templates/category/{category}")
async def api_delete_category(
    category: str,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
):
    """Delete all templates in a category."""
    await check_extension_enabled(wallet_info.wallet.user)
    count = await crud.delete_templates_by_category(wallet_info.wallet.user, category)
    # Return success even if count is 0 (idempotent delete)
    return {"deleted": count, "success": True}


class RenameCategoryPayload(BaseModel):
    new_category: str


@cyberherd_messaging_api_router.put("/api/v1/templates/category/{category}/rename")
async def api_rename_category(
    category: str,
    payload: RenameCategoryPayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
):
    """Rename a category."""
    await check_extension_enabled(wallet_info.wallet.user)
    count = await crud.rename_category(wallet_info.wallet.user, category, payload.new_category)
    if count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Category not found")
    return {"renamed": count, "new_category": payload.new_category}


# Generic template routes with {category}/{key} path parameters
@cyberherd_messaging_api_router.put("/api/v1/templates/{category}/{key}")
async def api_update_template(
    category: str,
    key: str,
    payload: MessageTemplatePayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
):
    await check_extension_enabled(wallet_info.wallet.user)
    success = await crud.update_message_template(
        wallet_info.wallet.user,
        category,
        key,
        payload.content,
        payload.reply_relay,
    )
    if not success:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Template not found")
    return {"updated": True}


@cyberherd_messaging_api_router.delete("/api/v1/templates/{category}/{key}")
async def api_delete_template(
    category: str,
    key: str,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
):
    await check_extension_enabled(wallet_info.wallet.user)
    success = await crud.delete_message_template(wallet_info.wallet.user, category, key)
    if not success:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Template not found")
    return {"deleted": True}


@cyberherd_messaging_api_router.get("/api/v1/templates/defaults")
async def api_get_defaults():
    return {"defaults": SEED_DEFAULTS}


@cyberherd_messaging_api_router.get("/api/v1/templates/export")
async def api_export_templates(
    fmt: str = "json",
    wallet_info: WalletTypeInfo = Depends(require_admin_key),
):
    """Export all message templates for the authenticated admin as a downloadable
    file. Supported formats:
    - json: application/json attachment with {category: {key: content}}
    - py: a Python file with top-level dict assignments for each category whose
      name is a valid Python identifier. Categories that are not valid
      identifiers are still included in the JSON export (use json format to
      preserve arbitrary category names).
    """
    await check_extension_enabled(wallet_info.wallet.user)
    # Gather templates for this user
    user_id = wallet_info.wallet.user
    templates = await crud.get_message_templates(user_id, None)
    mapping: dict[str, dict[str, str]] = {}
    for t in templates:
        mapping.setdefault(t.category, {})[str(t.key)] = t.content

    fmt_lower = (fmt or "").lower()
    if fmt_lower == "py":
        # Build a Python file with one top-level dict per category when the
        # category is a valid identifier. Use repr() for safe literal
        # representation of strings.
        lines: list[str] = ["# Exported CyberHerd Messaging templates\n# Generated by LNbits\n\n"]
        for category, inner in mapping.items():
            # Only include categories that are valid Python identifiers
            if not isinstance(category, str) or not category.isidentifier():
                # skip non-identifiers (these are available via JSON export)
                continue
            lines.append(f"{category} = {{\n")
            for key, content in inner.items():
                # keys may be numeric-like; write as strings in the literal
                lines.append(f"    {repr(str(key))}: {repr(content)},\n")
            lines.append("}\n\n")

        body = "".join(lines)
        from fastapi.responses import Response

        filename = f"cyberherd_templates_{user_id}.py"
        headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
        return Response(content=body, media_type="text/x-python", headers=headers)

    # Default: JSON export (round-trippable)
    from fastapi.responses import JSONResponse

    filename = f"cyberherd_templates_{user_id}.json"
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return JSONResponse(content=mapping, headers=headers)


@cyberherd_messaging_api_router.post("/api/v1/templates/defaults/import")
async def api_import_defaults(wallet_info: WalletTypeInfo = Depends(require_admin_key)):
    await check_extension_enabled(wallet_info.wallet.user)
    created = 0
    for category, mapping in SEED_DEFAULTS.items():
        for key, content in mapping.items():
            existing = await crud.get_message_template(wallet_info.wallet.user, category, key)
            if existing:
                continue
            # Support legacy string content or dicts with content + reply_relay
            if isinstance(content, dict):
                tpl_content = content.get('content') if 'content' in content else ''
                tpl_reply = content.get('reply_relay') if 'reply_relay' in content else None
            else:
                tpl_content = content
                tpl_reply = None

            await crud.create_message_template(wallet_info.wallet.user, category, key, tpl_content, tpl_reply)
            created += 1
    return {"imported": created}


def _parse_dicts_from_python(text: str) -> Dict[str, Dict[str, str]]:
    """Parse top-level dict assignments from a Python file safely using AST.
    Returns a mapping of variable name -> dict[str, str].
    Ignores any non-literal entries and non-string values.
    """
    result: Dict[str, Dict[str, str]] = {}
    try:
        tree = ast.parse(text)
    except Exception:
        return result

    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.value, ast.Dict):
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            # Ensure name is a valid string identifier
            if not name or not name.isidentifier():
                continue

            # Skip non-template dictionaries (those that don't contain string values)
            if name in ['goat_names_dict', 'herd_profile']:
                continue

            mapping: Dict[str, str] = {}
            for k_node, v_node in zip(node.value.keys, node.value.values):
                # Handle different key types and value types
                key_val = None
                val_val = None

                # Handle key
                if isinstance(k_node, ast.Constant):
                    if isinstance(k_node.value, (str, int)):
                        key_val = str(k_node.value)

                # Handle value - accept strings and convert other literals to strings
                if isinstance(v_node, ast.Constant):
                    if isinstance(v_node.value, str):
                        val_val = v_node.value
                    elif isinstance(v_node.value, (int, float, bool)):
                        val_val = str(v_node.value)
                elif isinstance(v_node, ast.List):
                    # Handle list values by joining them
                    list_items = []
                    for item in v_node.elts:
                        if isinstance(item, ast.Constant) and isinstance(item.value, str):
                            list_items.append(item.value)
                    if list_items:
                        val_val = ', '.join(list_items)

                if key_val is not None and val_val is not None:
                    mapping[key_val] = val_val

            if mapping:
                # Use the variable name as the category directly to keep imports generic
                result[name] = mapping
    return result


def _normalize_templates_payload(data: Any) -> Dict[str, Dict[str, str]]:
    """Normalize incoming data to {category: {key: content}} structure.
    Accepts either that exact structure, or a Python-like dict-of-dicts mapping from file.
    """
    if isinstance(data, dict):
        # Values must be dicts; keys of inner dict can be str or int; values must be str
        normalized: Dict[str, Dict[str, str]] = {}
        for cat, mapping in data.items():
            if not isinstance(cat, str) or not isinstance(mapping, dict):
                return {}
            inner: Dict[str, str] = {}
            for kk, vv in mapping.items():
                if isinstance(vv, str) and isinstance(kk, (str, int)):
                    inner[str(kk)] = vv
                else:
                    return {}
            normalized[cat] = inner
        return normalized
    return {}


@cyberherd_messaging_api_router.post("/api/v1/templates/import_file")
async def api_import_file(
    file: UploadFile = File(...),
    api_key: Optional[str] = Security(api_key_header),
    session_user_id: Optional[str] = Depends(optional_user_id),
):
    raw = (await file.read()).decode("utf-8", errors="ignore")

    payload: Dict[str, Dict[str, str]] = {}
    name_lower = (file.filename or "").lower()
    # Prefer Python parsing for .py files like messages.py
    if name_lower.endswith(".py"):
        payload = _parse_dicts_from_python(raw)
        if not payload:
            # Try JSON as a backup
            try:
                data = json.loads(raw)
                payload = _normalize_templates_payload(data)
            except Exception:
                payload = {}
    else:
        # Try JSON first for .json and others
        try:
            data = json.loads(raw)
            payload = _normalize_templates_payload(data)
        except Exception:
            payload = {}
        if not payload:
            payload = _parse_dicts_from_python(raw)

    if not payload:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Unsupported file format. Provide JSON {category: {key: content}} or a Python file with top-level dicts of strings.")

    # Determine the owning user for these templates.
    # Prefer API key (admin) when provided, otherwise use the logged-in session user.
    user_id: Optional[str] = None
    if api_key:
        wallet = await get_wallet_for_key(api_key)
        if wallet:
            user_id = wallet.user

    if not user_id and session_user_id:
        user_id = session_user_id

    if not user_id:
        # No authentication provided
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Missing authentication. Provide an admin API key or log in.")

    # Check if extension is enabled for this user
    await check_extension_enabled(user_id)

    created = 0
    updated = 0
    categories = set()
    for category, mapping in payload.items():
        # Ensure category is a string
        if not isinstance(category, str):
            continue
        categories.add(category)
        for key, content in mapping.items():
            existing = await crud.get_message_template(user_id, category, key)
            if existing:
                # update existing
                await crud.update_message_template(user_id, category, key, content)
                updated += 1
            else:
                await crud.create_message_template(user_id, category, key, content)
                created += 1

    return {"created": created, "updated": updated, "categories": sorted(list(categories))}


# Settings endpoints
class SettingsPayload(BaseModel):
    nostr_publishing_enabled: Optional[bool] = None
    nostr_private_key: Optional[str] = None
    clear_private_key: Optional[bool] = None


@cyberherd_messaging_api_router.get(
    "/api/v1/settings",
    summary="Get extension settings",
    description="Retrieves current extension settings. Public endpoint for reading settings."
)
async def api_get_settings(api_key: Optional[str] = Security(api_key_header)):
    """Get current extension settings.
    
    Public endpoint - no authentication required for reading settings.
    """
    val = await crud.get_setting("nostr_publishing_enabled")
    enabled = True if val is None else (str(val) not in ("0", "false", "False", "no", "off"))
    # Indicate whether a per-user key is set when admin key is provided
    nostr_key_set = False
    if api_key:
        wallet = await get_wallet_for_key(api_key)
        if wallet:
            user_key = await crud.get_user_setting(wallet.user, "nostr_private_key")
            nostr_key_set = bool(user_key)
    return {"nostr_publishing_enabled": enabled, "nostr_private_key_set": nostr_key_set}


@cyberherd_messaging_api_router.put(
    "/api/v1/settings",
    summary="Update extension settings",
    description="Updates extension settings. Requires admin key to prevent unauthorized configuration changes."
)
async def api_update_settings(
    payload: SettingsPayload,
    wallet_info: WalletTypeInfo = Depends(require_admin_key)
):
    """Update extension settings.
    
    Security: Requires admin key authentication to prevent:
    - Unauthorized settings changes
    - Disabling/enabling Nostr publishing without permission
    - Configuration tampering
    
    Settings changes affect the behavior of the extension and should only
    be performed by authorized administrators.
    """
    await check_extension_enabled(wallet_info.wallet.user)
    if payload.nostr_publishing_enabled is not None:
        await crud.set_setting(
            "nostr_publishing_enabled", "1" if payload.nostr_publishing_enabled else "0"
        )

    # Handle per-user private key set/clear
    if payload.clear_private_key:
        await crud.delete_user_setting(wallet_info.wallet.user, "nostr_private_key")
    elif payload.nostr_private_key:
        # Normalize and store sanitized hex
        from . import services as _services
        hex_key, key_len, key_err = _services._prepare_private_key(payload.nostr_private_key)  # type: ignore[attr-defined]
        if key_err or not hex_key:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Invalid Nostr private key ({key_err or 'invalid'})")
        await crud.set_user_setting(wallet_info.wallet.user, "nostr_private_key", hex_key)

    # Return settings including key presence for this user
    return await api_get_settings(wallet_info.wallet.adminkey)

__all__ = ["cyberherd_messaging_api_router"]
