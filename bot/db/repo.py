from datetime import datetime, timedelta

import aiosqlite


# ─── helpers ─────────────────────────────────────────────────────────────────


def _now() -> str:
    return datetime.utcnow().isoformat()


# ─── users ───────────────────────────────────────────────────────────────────


async def upsert_user(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    db_path: str,
) -> None:
    now = _now()
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_seen  = excluded.last_seen
        """,
            (telegram_id, username, first_name, now, now),
        )
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
        await db.execute(
            """
            INSERT INTO subscriptions
                (telegram_id, product_id, status, active_until, order_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id, product_id) DO UPDATE SET
                status       = excluded.status,
                active_until = COALESCE(excluded.active_until, active_until),
                order_id     = COALESCE(excluded.order_id, order_id),
                updated_at   = excluded.updated_at
        """,
            (telegram_id, product_id, status, active_until, order_id, now, now),
        )
        await db.commit()


async def activate_subscription(
    telegram_id: int,
    product_id: str,
    order_id: str,
    db_path: str,
    days: int = 30,
) -> None:
    """Activate subscription, extending from MAX(existing active_until, now) + days."""
    now = datetime.utcnow()
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT active_until FROM subscriptions WHERE telegram_id = ? AND product_id = ?",
            (telegram_id, product_id),
        ) as cur:
            row = await cur.fetchone()
        if row and row[0]:
            try:
                base = max(datetime.fromisoformat(row[0]), now)
            except (ValueError, TypeError):
                base = now
        else:
            base = now
        until = (base + timedelta(days=days)).isoformat()
        now_str = now.isoformat()
        await db.execute(
            """
            INSERT INTO subscriptions
                (telegram_id, product_id, status, active_until, order_id, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?, ?, ?)
            ON CONFLICT(telegram_id, product_id) DO UPDATE SET
                status       = 'active',
                active_until = excluded.active_until,
                order_id     = excluded.order_id,
                updated_at   = excluded.updated_at
        """,
            (telegram_id, product_id, until, order_id, now_str, now_str),
        )
        await db.commit()


async def set_subscription_status(
    telegram_id: int, product_id: str, status: str, db_path: str
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE subscriptions SET status = ?, updated_at = ?
            WHERE telegram_id = ? AND product_id = ?
        """,
            (status, _now(), telegram_id, product_id),
        )
        await db.commit()


async def create_product(db_path: str, data: dict) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO products (product_id, name, description, channel_id, discussion_id, prodamus_url, price, subscription_id)
            VALUES (:product_id, :name, :description, :channel_id, :discussion_id, :prodamus_url, :price, :subscription_id)
        """,
            data,
        )
        await db.commit()


async def update_product(db_path: str, product_id: str, data: dict) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE products SET
                name            = :name,
                description     = :description,
                channel_id      = :channel_id,
                discussion_id   = :discussion_id,
                prodamus_url    = :prodamus_url,
                price           = :price,
                subscription_id = :subscription_id
            WHERE product_id = :product_id
        """,
            {**data, "product_id": product_id},
        )
        await db.commit()


async def delete_product(db_path: str, product_id: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        await db.commit()


async def get_expired_active_subscriptions(db_path: str) -> list[dict]:
    """Active subs past active_until + 2-day grace period (for Prodamus rebill lag)."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT s.*, p.channel_id, p.discussion_id, p.name AS product_name
            FROM subscriptions s
            JOIN products p USING (product_id)
            WHERE s.status = 'active' AND s.active_until < datetime('now', '-2 days')
        """
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ─── admin queries ────────────────────────────────────────────────────────────


async def get_active_subscriptions(db_path: str) -> list[dict]:
    """Active subscriptions joined with user info, ordered by active_until.

    Replaces the internal _get_active_subs hack from the old admin handler.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT s.*, u.username, u.first_name
            FROM subscriptions s
            LEFT JOIN users u USING (telegram_id)
            WHERE s.status = 'active'
            ORDER BY s.active_until
        """
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_stats(db_path: str) -> dict:
    """Aggregate counts for /admin_stats dashboard."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total_users: int = (await cur.fetchone() or (0,))[0]
        async with db.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
        ) as cur:
            active: int = (await cur.fetchone() or (0,))[0]
        async with db.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE status IN ('expired', 'cancelled')"
        ) as cur:
            expired_cancelled: int = (await cur.fetchone() or (0,))[0]
        async with db.execute(
            "SELECT COUNT(*) FROM subscriptions "
            "WHERE status = 'active' AND active_until < datetime('now', '+3 days')"
        ) as cur:
            expiring_3d: int = (await cur.fetchone() or (0,))[0]
    return {
        "total_users": total_users,
        "active": active,
        "expired_cancelled": expired_cancelled,
        "expiring_3d": expiring_3d,
    }


async def get_expiring_subscriptions(db_path: str, days: int) -> list[dict]:
    """Active subscriptions expiring within `days` days, joined with user and product info."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT s.telegram_id, s.product_id, s.active_until,
                   u.username, u.first_name, p.name AS product_name
            FROM subscriptions s
            LEFT JOIN users u USING (telegram_id)
            LEFT JOIN products p USING (product_id)
            WHERE s.status = 'active'
              AND s.active_until < datetime('now', '+' || ? || ' days')
            ORDER BY s.active_until
        """,
            (str(days),),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def find_user(db_path: str, query: str) -> dict | None:
    """Find a user by @username, username (without @), or numeric tg_id.

    Returns the user row extended with a 'subscriptions' list, or None.
    Each subscription item includes: product_id, name, status, active_until.
    """
    clean = query.lstrip("@").strip()
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        if clean.isdigit():
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (int(clean),)
            ) as cur:
                row = await cur.fetchone()
        else:
            async with db.execute(
                "SELECT * FROM users WHERE username = ?", (clean,)
            ) as cur:
                row = await cur.fetchone()
        if row is None:
            return None
        user = dict(row)
        async with db.execute(
            """
            SELECT s.product_id, s.status, s.active_until, p.name
            FROM subscriptions s
            LEFT JOIN products p USING (product_id)
            WHERE s.telegram_id = ?
        """,
            (user["telegram_id"],),
        ) as cur:
            subs = await cur.fetchall()
        user["subscriptions"] = [dict(s) for s in subs]
        return user
