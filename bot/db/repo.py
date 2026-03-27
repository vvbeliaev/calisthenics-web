from datetime import datetime, timedelta

import aiosqlite


# ─── helpers ─────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.utcnow().isoformat()


def _active_until(days: int = 30) -> str:
    return (datetime.utcnow() + timedelta(days=days)).isoformat()


# ─── users ───────────────────────────────────────────────────────────────────

async def upsert_user(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    db_path: str,
) -> None:
    now = _now()
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, first_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_seen  = excluded.last_seen
        """, (telegram_id, username, first_name, now, now))
        await db.commit()


# ─── products ────────────────────────────────────────────────────────────────

async def get_all_products(db_path: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM products") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_product(product_id: str, db_path: str) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM products WHERE product_id = ?", (product_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ─── subscriptions ───────────────────────────────────────────────────────────

async def get_subscriptions(telegram_id: int, db_path: str) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE telegram_id = ?", (telegram_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_subscription(
    telegram_id: int, product_id: str, db_path: str
) -> dict | None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE telegram_id = ? AND product_id = ?",
            (telegram_id, product_id),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def upsert_subscription(
    telegram_id: int,
    product_id: str,
    status: str,
    active_until: str | None = None,
    order_id: str | None = None,
    db_path: str = "",
) -> None:
    now = _now()
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO subscriptions
                (telegram_id, product_id, status, active_until, order_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id, product_id) DO UPDATE SET
                status       = excluded.status,
                active_until = COALESCE(excluded.active_until, active_until),
                order_id     = COALESCE(excluded.order_id, order_id),
                updated_at   = excluded.updated_at
        """, (telegram_id, product_id, status, active_until, order_id, now, now))
        await db.commit()


async def activate_subscription(
    telegram_id: int, product_id: str, order_id: str, db_path: str
) -> None:
    """Успешная оплата — ставим active + продлеваем на 30 дней."""
    now = _now()
    until = _active_until(30)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            INSERT INTO subscriptions
                (telegram_id, product_id, status, active_until, order_id, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?, ?, ?)
            ON CONFLICT(telegram_id, product_id) DO UPDATE SET
                status       = 'active',
                active_until = excluded.active_until,
                order_id     = excluded.order_id,
                updated_at   = excluded.updated_at
        """, (telegram_id, product_id, until, order_id, now, now))
        await db.commit()


async def set_subscription_status(
    telegram_id: int, product_id: str, status: str, db_path: str
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            UPDATE subscriptions SET status = ?, updated_at = ?
            WHERE telegram_id = ? AND product_id = ?
        """, (status, _now(), telegram_id, product_id))
        await db.commit()


async def get_expired_active_subscriptions(db_path: str) -> list[dict]:
    """Активные подписки с истёкшим active_until — для APScheduler."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT s.*, p.channel_id, p.discussion_id, p.name AS product_name
            FROM subscriptions s
            JOIN products p USING (product_id)
            WHERE s.status = 'active' AND s.active_until < datetime('now')
        """) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
