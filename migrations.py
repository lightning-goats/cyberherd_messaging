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
        except Exception:
            # Column likely already exists, ignore
            pass
