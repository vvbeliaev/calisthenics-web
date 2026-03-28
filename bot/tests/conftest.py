"""Shared pytest fixtures for bot tests."""

import pytest
import aiosqlite


@pytest.fixture
async def db(tmp_path):
    """SQLite DB with full schema, returned as a path string."""
    db_path = str(tmp_path / "test.db")
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            CREATE TABLE products (
                product_id    TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                description   TEXT,
                channel_id    INTEGER NOT NULL,
                discussion_id INTEGER NOT NULL,
                prodamus_url  TEXT NOT NULL,
                price         INTEGER NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE users (
                telegram_id   INTEGER PRIMARY KEY,
                username      TEXT,
                first_name    TEXT,
                first_seen    TEXT NOT NULL,
                last_seen     TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE subscriptions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id   INTEGER NOT NULL,
                product_id    TEXT NOT NULL REFERENCES products(product_id),
                active_until  TEXT,
                order_id      TEXT,
                status        TEXT NOT NULL DEFAULT 'pending',
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL,
                UNIQUE(telegram_id, product_id)
            )
        """)
        await conn.commit()
    return db_path
