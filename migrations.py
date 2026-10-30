from lnbits.db import Database

db = Database("ext_cyberherd_messaging")


async def m001_create_message_templates(db):
    """Create message_templates table (portable SQLite/Postgres).

    Mirrors common LNbits pattern: simple engine check (db.type) and minimal divergent DDL.
    Avoids AUTOINCREMENT (not portable) and uses BIGSERIAL on Postgres for auto increment.
    """
    if db.type in {"POSTGRES", "COCKROACH"}:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cyberherd_messaging.message_templates (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, category, key)
            );
        """)
    else:  # sqlite
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cyberherd_messaging.message_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, category, key)
            );
        """)


async def m002_create_settings(db):
    """Create a simple key-value settings table for the extension.

    Used for global toggles like enabling/disabling Nostr publishing.
    """
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cyberherd_messaging.settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    # Seed default: nostr publishing enabled
    if db.type in {"POSTGRES", "COCKROACH"}:
        await db.execute(
            """
            INSERT INTO cyberherd_messaging.settings(key, value)
            VALUES('nostr_publishing_enabled', '1')
            ON CONFLICT (key) DO NOTHING;
            """
        )
    else:  # sqlite
        await db.execute(
            """
            INSERT OR IGNORE INTO cyberherd_messaging.settings(key, value)
            VALUES('nostr_publishing_enabled', '1');
            """
        )


async def m003_create_user_settings(db):
    """Create per-user settings table to store secrets like nostr_private_key.

    Schema: cyberherd_messaging.user_settings(user_id TEXT, key TEXT, value TEXT,
            PRIMARY KEY(user_id, key))
    """
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cyberherd_messaging.user_settings (
            user_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (user_id, key)
        );
        """
    )


async def m004_add_reply_relay_column(db):
    """Add reply_relay column to message_templates table.
    
    This column stores the relay URL to use when publishing replies to Nostr.
    """
    if db.type in {"POSTGRES", "COCKROACH"}:
        await db.execute(
            """
            ALTER TABLE cyberherd_messaging.message_templates
            ADD COLUMN IF NOT EXISTS reply_relay TEXT;
            """
        )
    else:  # sqlite
        # SQLite doesn't support IF NOT EXISTS in ALTER TABLE
        # Check if column exists first
        try:
            await db.execute(
                """
                ALTER TABLE cyberherd_messaging.message_templates
                ADD COLUMN reply_relay TEXT;
                """
            )
        except Exception as exc:
            # Only ignore "column already exists"; re-raise anything else so a
            # real migration failure is not silently swallowed.
            msg = str(exc).lower()
            if "duplicate column" in msg or "already exists" in msg:
                pass
            else:
                raise


async def m005_seed_member_message_templates(db):
    """Install editable member notices for existing owners; new owners seed lazily."""
    from .crud import ensure_default_templates

    owners = await db.fetchall(
        f"SELECT user_id FROM {db.references_schema}message_templates UNION "
        f"SELECT user_id FROM {db.references_schema}user_settings"
    )
    for owner in owners:
        if owner["user_id"]:
            await ensure_default_templates(owner["user_id"], database=db)


async def m006_seed_treat_breakdown_template(db):
    """Add an editable score footer without changing existing message wording."""
    from .crud import ensure_treat_breakdown_template

    owners = await db.fetchall(
        f"SELECT user_id FROM {db.references_schema}message_templates UNION "
        f"SELECT user_id FROM {db.references_schema}user_settings"
    )
    for owner in owners:
        if owner["user_id"]:
            await ensure_treat_breakdown_template(owner["user_id"], database=db)


async def m007_seed_context_summary_templates(db):
    """Install editable score summaries for membership, rejection and feeder notices."""
    from .crud import ensure_context_summary_templates

    owners = await db.fetchall(
        f"SELECT user_id FROM {db.references_schema}message_templates UNION "
        f"SELECT user_id FROM {db.references_schema}user_settings"
    )
    for owner in owners:
        if owner["user_id"]:
            await ensure_context_summary_templates(owner["user_id"], database=db)


async def m008_seed_zap_request_template(db):
    """Install editable NIP-57 request comments; never change signer permissions."""
    from .crud import ensure_zap_request_template

    owners = await db.fetchall(
        f"SELECT user_id FROM {db.references_schema}message_templates UNION "
        f"SELECT user_id FROM {db.references_schema}user_settings"
    )
    for owner in owners:
        if owner["user_id"]:
            await ensure_zap_request_template(owner["user_id"], database=db)


async def m009_seed_stream_chat_templates(db):
    """Install stream invitations, command outcomes and operator pause notices."""
    from .crud import ensure_stream_chat_templates

    owners = await db.fetchall(
        f"SELECT user_id FROM {db.references_schema}message_templates UNION "
        f"SELECT user_id FROM {db.references_schema}user_settings"
    )
    for owner in owners:
        if owner["user_id"]:
            await ensure_stream_chat_templates(owner["user_id"], database=db)


async def refresh_feeder_availability_templates(db, *, schema=None):
    """Replace known stock wording and add variants without overwriting custom rows."""
    from .defaults import LEGACY_FEEDER_AVAILABILITY_TEMPLATES, STREAM_CHAT_NOTICES

    schema = schema or db.references_schema
    owners = await db.fetchall(
        f"SELECT DISTINCT user_id FROM {schema}message_templates "
        "WHERE category IN ('feeder_requests_paused','feeder_requests_enabled')"
    )
    for owner in owners:
        uid = owner["user_id"]
        marker = "feeder_availability_templates_v2"
        if await db.fetchone(
            f"SELECT value FROM {schema}user_settings WHERE user_id=:uid AND key=:key",
            {"uid": uid, "key": marker},
        ):
            continue
        for category, old_templates in LEGACY_FEEDER_AVAILABILITY_TEMPLATES.items():
            if not await db.fetchone(
                f"SELECT id FROM {schema}message_templates WHERE user_id=:uid AND category=:category",
                {"uid": uid, "category": category},
            ):
                continue
            for key, content in STREAM_CHAT_NOTICES[category].items():
                values = {"uid": uid, "category": category, "key": key, "content": content}
                if key in old_templates:
                    await db.execute(
                        f"UPDATE {schema}message_templates SET content=:content, updated_at=CURRENT_TIMESTAMP "
                        "WHERE user_id=:uid AND category=:category AND key=:key AND content=:old",
                        {**values, "old": old_templates[key]},
                    )
                else:
                    await db.execute(
                        f"""INSERT INTO {schema}message_templates (user_id,category,key,content)
                        VALUES (:uid,:category,:key,:content) ON CONFLICT (user_id,category,key) DO NOTHING""",
                        values,
                    )
        await db.execute(
            f"INSERT INTO {schema}user_settings (user_id,key,value) VALUES (:uid,:key,'1') "
            "ON CONFLICT (user_id,key) DO NOTHING",
            {"uid": uid, "key": marker},
        )


async def m010_refresh_feeder_availability_templates(db):
    # LNbits supplies the transaction connection to migration entry points.
    await refresh_feeder_availability_templates(db)


async def expand_message_variations(db, *, schema=None):
    """Add requested variants once, preserving edits and category opt-outs."""
    from .defaults import MESSAGE_VARIATIONS, LEGACY_UNCERTAIN_FEEDER_MESSAGE

    schema = schema or db.references_schema
    owners = await db.fetchall(f"SELECT DISTINCT user_id FROM {schema}message_templates")
    for owner in owners:
        uid = owner["user_id"]
        marker = "expanded_message_variations_v1"
        if await db.fetchone(
            f"SELECT value FROM {schema}user_settings WHERE user_id=:uid AND key=:key",
            {"uid": uid, "key": marker},
        ):
            continue
        for category, variants in MESSAGE_VARIATIONS.items():
            if not await db.fetchone(
                f"SELECT id FROM {schema}message_templates WHERE user_id=:uid AND category=:category",
                {"uid": uid, "category": category},
            ):
                continue
            for key, content in variants.items():
                values = {"uid": uid, "category": category, "key": key, "content": content}
                if category == "feeder_outcome_uncertain" and key == "0":
                    await db.execute(
                        f"UPDATE {schema}message_templates SET content=:content,updated_at=CURRENT_TIMESTAMP "
                        "WHERE user_id=:uid AND category=:category AND key=:key AND content=:old",
                        {**values, "old": LEGACY_UNCERTAIN_FEEDER_MESSAGE},
                    )
                else:
                    await db.execute(
                        f"INSERT INTO {schema}message_templates (user_id,category,key,content) "
                        "VALUES (:uid,:category,:key,:content) ON CONFLICT (user_id,category,key) DO NOTHING",
                        values,
                    )
        await db.execute(
            f"INSERT INTO {schema}user_settings (user_id,key,value) VALUES (:uid,:key,'1') "
            "ON CONFLICT (user_id,key) DO NOTHING",
            {"uid": uid, "key": marker},
        )


async def m011_expand_message_variations(db):
    # LNbits supplies the transaction connection to migration entry points.
    await expand_message_variations(db)


async def seed_evening_pause_templates(db, *, schema=None):
    """Install the new evening category once; never restore later deletions."""
    from .defaults import EVENING_PAUSE_TEMPLATES

    schema = schema or db.references_schema
    owners = await db.fetchall(
        f"SELECT user_id FROM {schema}message_templates UNION "
        f"SELECT user_id FROM {schema}user_settings"
    )
    marker = "evening_pause_templates_v1"
    for owner in owners:
        uid = owner["user_id"]
        if not uid or await db.fetchone(
            f"SELECT value FROM {schema}user_settings WHERE user_id=:uid AND key=:key",
            {"uid": uid, "key": marker},
        ):
            continue
        for key, content in EVENING_PAUSE_TEMPLATES.items():
            await db.execute(
                f"INSERT INTO {schema}message_templates (user_id,category,key,content) "
                "VALUES (:uid,'feeder_requests_paused_night',:key,:content) "
                "ON CONFLICT (user_id,category,key) DO NOTHING",
                {"uid": uid, "key": key, "content": content},
            )
        await db.execute(
            f"INSERT INTO {schema}user_settings (user_id,key,value) VALUES (:uid,:key,'1') "
            "ON CONFLICT (user_id,key) DO NOTHING",
            {"uid": uid, "key": marker},
        )


async def m012_seed_evening_pause_templates(db):
    # LNbits supplies the transaction connection to migration entry points.
    await seed_evening_pause_templates(db)
