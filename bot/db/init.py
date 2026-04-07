import aiosqlite


async def init_tables(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id      TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                description     TEXT,
                channel_id      INTEGER NOT NULL,
                discussion_id   INTEGER NOT NULL,
                prodamus_url    TEXT NOT NULL,
                price           INTEGER NOT NULL,
                subscription_id INTEGER NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id   INTEGER PRIMARY KEY,
                username      TEXT,
                first_name    TEXT,
                first_seen    TEXT NOT NULL,
                last_seen     TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id         INTEGER NOT NULL,
                product_id          TEXT NOT NULL REFERENCES products(product_id),
                active_until        TEXT,
                order_id            TEXT,
                status              TEXT NOT NULL DEFAULT 'pending',
                created_at          TEXT NOT NULL,
                updated_at          TEXT NOT NULL,
                UNIQUE(telegram_id, product_id)
            )
        """)
        await db.commit()
