"""Tests for admin-specific repo functions."""

from datetime import datetime, timedelta

import aiosqlite
import pytest

from db import repo


def _now() -> str:
    return datetime.utcnow().isoformat()


def _days(n: int) -> str:
    return (datetime.utcnow() + timedelta(days=n)).isoformat()


@pytest.fixture
async def populated_db(db):
    """DB fixture pre-loaded with known users and subscriptions."""
    async with aiosqlite.connect(db) as conn:
        await conn.executemany(
            "INSERT INTO products VALUES (?,?,?,?,?,?,?)",
            [
                ("base", "Базовый", None, 1001, 2001, "https://pay.test/base", 2990),
                ("adv",  "Продвинутый", None, 1002, 2002, "https://pay.test/adv", 4990),
            ],
        )
        await conn.executemany(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            [
                (1, "alice",   "Alice",   _now(), _now()),
                (2, "bob",     "Bob",     _now(), _now()),
                (3, None,      "Charlie", _now(), _now()),  # no username
            ],
        )
        await conn.executemany(
            "INSERT INTO subscriptions "
            "(telegram_id, product_id, status, active_until, order_id, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            [
                (1, "base", "active",  _days(20), "ord1", _now(), _now()),  # alice, expires 20d
                (2, "base", "active",  _days(5),  "ord2", _now(), _now()),  # bob,   expires 5d
                (2, "adv",  "pending", None,       None,   _now(), _now()),  # bob,   pending
                (3, "base", "expired", _days(-1), "ord3", _now(), _now()),  # charlie, expired
            ],
        )
        await conn.commit()
    return db


async def test_get_active_subscriptions_returns_only_active(populated_db):
    subs = await repo.get_active_subscriptions(populated_db)
    assert len(subs) == 2
    assert all(s["status"] == "active" for s in subs)


async def test_get_active_subscriptions_includes_username(populated_db):
    subs = await repo.get_active_subscriptions(populated_db)
    usernames = {s["username"] for s in subs}
    assert "alice" in usernames
    assert "bob" in usernames


async def test_get_stats(populated_db):
    s = await repo.get_stats(populated_db)
    assert s["total_users"] == 3
    assert s["active"] == 2
    assert s["pending"] == 1
    assert s["expired_cancelled"] == 1
    assert s["expiring_7d"] == 1  # only bob (5 days)


async def test_get_expiring_subscriptions_7d(populated_db):
    results = await repo.get_expiring_subscriptions(populated_db, days=7)
    assert len(results) == 1
    assert results[0]["telegram_id"] == 2
    assert results[0]["username"] == "bob"


async def test_get_expiring_subscriptions_wider_window(populated_db):
    results = await repo.get_expiring_subscriptions(populated_db, days=30)
    assert len(results) == 2  # alice (20d) and bob (5d)


async def test_find_user_by_username_with_at(populated_db):
    user = await repo.find_user(populated_db, "@alice")
    assert user is not None
    assert user["telegram_id"] == 1
    assert len(user["subscriptions"]) == 1
    assert user["subscriptions"][0]["product_id"] == "base"


async def test_find_user_by_username_without_at(populated_db):
    user = await repo.find_user(populated_db, "alice")
    assert user is not None
    assert user["telegram_id"] == 1


async def test_find_user_by_tg_id(populated_db):
    user = await repo.find_user(populated_db, "2")
    assert user is not None
    assert user["username"] == "bob"
    assert len(user["subscriptions"]) == 2


async def test_find_user_not_found(populated_db):
    user = await repo.find_user(populated_db, "nonexistent")
    assert user is None
