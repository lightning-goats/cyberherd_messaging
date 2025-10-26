from typing import Optional

from lnbits.db import Database

from .models import MessageTemplate

db = Database("ext_cyberherd_messaging")


async def get_message_templates(user_id: Optional[str], category: Optional[str] = None) -> list[MessageTemplate]:
    """Get message templates.

    If user_id is provided, return templates for that user. If user_id is None,
    return templates across all users (public read access).
    """
    params: dict = {}
    if user_id:
        query = "SELECT * FROM cyberherd_messaging.message_templates WHERE user_id = :user_id"
        params["user_id"] = user_id
    else:
        query = "SELECT * FROM cyberherd_messaging.message_templates"

    if category:
        if params:
            query += " AND category = :category"
        else:
            query += " WHERE category = :category"
        params["category"] = category

    query += " ORDER BY category, key"
    rows = await db.fetchall(query, params)
    return [MessageTemplate(**row) for row in rows]


async def get_message_template(user_id: str, category: str, key: str) -> Optional[MessageTemplate]:
    """Get a specific message template."""
    row = await db.fetchone(
        "SELECT * FROM cyberherd_messaging.message_templates WHERE user_id = :user_id AND category = :category AND key = :key",
        {"user_id": user_id, "category": category, "key": key}
    )
    return MessageTemplate(**row) if row else None


async def create_message_template(
    user_id: str,
    category: str,
    key: str,
    content: str,
    reply_relay: Optional[str] = None,
) -> MessageTemplate:
    """Create a new message template."""
    async with db.connect() as conn:
        await conn.execute(
            """
            INSERT INTO cyberherd_messaging.message_templates (
                user_id, category, key, content, reply_relay
            )
            VALUES (:user_id, :category, :key, :content, :reply_relay)
            """,
            {
                "user_id": user_id,
                "category": category,
                "key": key,
                "content": content,
                "reply_relay": reply_relay,
            },
        )
        # Get the newly created template with all fields including timestamps
        row = await conn.fetchone(
            """
            SELECT *
            FROM cyberherd_messaging.message_templates
            WHERE user_id = :user_id AND category = :category AND key = :key
            """,
            {"user_id": user_id, "category": category, "key": key},
        )
        return MessageTemplate(**row)


async def update_message_template(
    user_id: str,
    category: str,
    key: str,
    content: str,
    reply_relay: Optional[str] = None,
) -> bool:
    """Update an existing message template."""
    result = await db.execute(
        """
        UPDATE cyberherd_messaging.message_templates
        SET content = :content,
            reply_relay = :reply_relay,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = :user_id AND category = :category AND key = :key
        """,
        {
            "user_id": user_id,
            "category": category,
            "key": key,
            "content": content,
            "reply_relay": reply_relay,
        },
    )
    return result.rowcount > 0


# Settings helpers
async def get_setting(key: str) -> Optional[str]:
    row = await db.fetchone(
        "SELECT value FROM cyberherd_messaging.settings WHERE key = :key",
        {"key": key},
    )
    return row["value"] if row else None


async def set_setting(key: str, value: str) -> None:
    await db.execute(
        """
        INSERT INTO cyberherd_messaging.settings(key, value)
        VALUES (:key, :value)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        {"key": key, "value": value},
    )


async def delete_message_template(user_id: str, category: str, key: str) -> bool:
    """Delete a message template."""
    result = await db.execute(
        "DELETE FROM cyberherd_messaging.message_templates WHERE user_id = :user_id AND category = :category AND key = :key",
        {"user_id": user_id, "category": category, "key": key}
    )
    return result.rowcount > 0


async def delete_templates_by_category(user_id: str, category: str) -> int:
    """Delete all templates in a category for a user. Returns count of deleted templates."""
    result = await db.execute(
        "DELETE FROM cyberherd_messaging.message_templates WHERE user_id = :user_id AND category = :category",
        {"user_id": user_id, "category": category}
    )
    return result.rowcount


async def rename_category(user_id: str, old_category: str, new_category: str) -> int:
    """Rename a category for a user. Returns count of updated templates."""
    result = await db.execute(
        "UPDATE cyberherd_messaging.message_templates SET category = :new_category, updated_at = CURRENT_TIMESTAMP WHERE user_id = :user_id AND category = :old_category",
        {"user_id": user_id, "old_category": old_category, "new_category": new_category}
    )
    return result.rowcount


# Per-user settings helpers (for secrets like nostr_private_key)
async def get_user_setting(user_id: str, key: str) -> Optional[str]:
    row = await db.fetchone(
        "SELECT value FROM cyberherd_messaging.user_settings WHERE user_id = :user_id AND key = :key",
        {"user_id": user_id, "key": key},
    )
    return row["value"] if row else None


async def set_user_setting(user_id: str, key: str, value: str) -> None:
    await db.execute(
        """
        INSERT INTO cyberherd_messaging.user_settings(user_id, key, value)
        VALUES (:user_id, :key, :value)
        ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value
        """,
        {"user_id": user_id, "key": key, "value": value},
    )


async def delete_user_setting(user_id: str, key: str) -> None:
    await db.execute(
        "DELETE FROM cyberherd_messaging.user_settings WHERE user_id = :user_id AND key = :key",
        {"user_id": user_id, "key": key},
    )
