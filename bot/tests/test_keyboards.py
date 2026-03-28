"""Tests for admin keyboard builders and text formatters."""

from aiogram.types import InlineKeyboardMarkup
from handlers.admin.keyboards import (
    PAGE_SIZE,
    admin_list_kb,
    format_list_page,
    format_user_card,
    payment_notification_kb,
    payment_revoke_confirm_kb,
    user_card_kb,
)


# ── keyboard builders ──────────────────────────────────────────────────────────


def test_payment_notification_kb_has_grant_and_revoke():
    kb = payment_notification_kb(tg_id=12345, product_id="base")
    assert isinstance(kb, InlineKeyboardMarkup)
    cb = {b.callback_data for row in kb.inline_keyboard for b in row}
    assert "apay_grant:12345:base" in cb
    assert "apay_revoke:12345:base" in cb


def test_payment_revoke_confirm_kb_has_confirm_and_cancel():
    kb = payment_revoke_confirm_kb(tg_id=12345, product_id="base")
    cb = {b.callback_data for row in kb.inline_keyboard for b in row}
    assert "apay_revoke_confirm:12345:base" in cb
    assert "apay_revoke_cancel:12345:base" in cb


def test_user_card_kb_active_gets_revoke_inactive_gets_grant():
    subs = [{"product_id": "base", "status": "active"}]
    products = [
        {"product_id": "base", "name": "Базовый"},
        {"product_id": "adv", "name": "Продвинутый"},
    ]
    kb = user_card_kb(tg_id=99, subscriptions=subs, all_products=products)
    cb = {b.callback_data for row in kb.inline_keyboard for b in row}
    assert "afind_revoke:99:base" in cb
    assert "afind_grant:99:adv" in cb


def test_admin_list_kb_first_page_no_back():
    kb = admin_list_kb(offset=0, total=50, page_size=20)
    cb = [b.callback_data for row in kb.inline_keyboard for b in row if b.callback_data]
    assert "alist:20" in cb
    assert not any(c == "alist:-20" for c in cb)


def test_admin_list_kb_middle_page_has_both_directions():
    kb = admin_list_kb(offset=20, total=50, page_size=20)
    cb = [b.callback_data for row in kb.inline_keyboard for b in row if b.callback_data]
    assert "alist:0" in cb
    assert "alist:40" in cb


def test_admin_list_kb_last_page_no_forward():
    kb = admin_list_kb(offset=40, total=50, page_size=20)
    cb = [b.callback_data for row in kb.inline_keyboard for b in row if b.callback_data]
    assert "alist:20" in cb
    assert "alist:60" not in cb


# ── text formatters ────────────────────────────────────────────────────────────


def test_format_list_page_shows_username_and_product():
    subs = [
        {
            "username": "alice",
            "telegram_id": 1,
            "product_id": "base",
            "active_until": "2026-04-15T00:00:00",
        },
    ]
    text = format_list_page(subs, offset=0, total=1)
    assert "@alice" in text
    assert "base" in text
    assert "2026-04-15" in text


def test_format_list_page_uses_id_when_no_username():
    subs = [
        {
            "username": None,
            "telegram_id": 99,
            "product_id": "adv",
            "active_until": "2026-05-01T00:00:00",
        },
    ]
    text = format_list_page(subs, offset=0, total=1)
    assert "id:99" in text


def test_format_user_card_shows_subscriptions():
    user = {
        "telegram_id": 1,
        "username": "alice",
        "first_name": "Alice",
        "first_seen": "2026-01-01T00:00:00",
        "last_seen": "2026-03-27T00:00:00",
        "subscriptions": [
            {
                "product_id": "base",
                "name": "Базовый",
                "status": "active",
                "active_until": "2026-04-15T00:00:00",
            },
        ],
    }
    text = format_user_card(user)
    assert "@alice" in text
    assert "Базовый" in text
    assert "active" in text
