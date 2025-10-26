from lnbits.db import Database


async def m001_create_message_templates(db: Database):
    """Create message_templates table (portable SQLite/Postgres).

    Mirrors common LNbits pattern: simple engine check (db.type) and minimal divergent DDL.
    Avoids AUTOINCREMENT (not portable) and uses BIGSERIAL on Postgres for auto increment.
    """
    backend = (getattr(db, "type", "") or "").lower()
    if backend == "postgres":
        ddl = """
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
        """
    else:  # sqlite
        ddl = """
            CREATE TABLE IF NOT EXISTS cyberherd_messaging.message_templates (
                id INTEGER PRIMARY KEY,  -- rowid alias auto-increments in SQLite
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, category, key)
            );
        """

    await db.execute(ddl)
