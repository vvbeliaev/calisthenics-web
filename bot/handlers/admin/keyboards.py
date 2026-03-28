"""Admin keyboard builders and text formatters.

All functions are pure — no I/O, no bot calls, no settings access.
Both keyboard builders and text formatters live here because they are
presentation-only logic shared between commands.py and callbacks.py.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PAGE_SIZE = 20


# ── keyboard builders ──────────────────────────────────────────────────────────

def payment_notification_kb(tg_id: int, product_id: str) -> InlineKeyboardMarkup:
    """Attached to the admin payment notification message."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Выдать доступ",
            callback_data=f"apay_grant:{tg_id}:{product_id}",
        ),
        InlineKeyboardButton(
            text="❌ Отозвать",
            callback_data=f"apay_revoke:{tg_id}:{product_id}",
        ),
    ]])


def payment_revoke_confirm_kb(tg_id: int, product_id: str) -> InlineKeyboardMarkup:
    """Two-step confirmation before revoking a just-paid subscription."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Да, отозвать",
            callback_data=f"apay_revoke_confirm:{tg_id}:{product_id}",
        ),
        InlineKeyboardButton(
            text="Отмена",
            callback_data=f"apay_revoke_cancel:{tg_id}:{product_id}",
        ),
    ]])


def user_card_kb(
    tg_id: int,
    subscriptions: list[dict],
    all_products: list[dict],
) -> InlineKeyboardMarkup:
    """Per-product action buttons on a /admin_find user card.

    Active subscription → Revoke button.
    Non-active or absent → Grant button.
    """
    sub_map = {s["product_id"]: s["status"] for s in subscriptions}
    rows = []
    for product in all_products:
        pid = product["product_id"]
        name = product["name"]
        if sub_map.get(pid) == "active":
            rows.append([InlineKeyboardButton(
                text=f"❌ Отозвать: {name}",
                callback_data=f"afind_revoke:{tg_id}:{pid}",
            )])
        else:
            rows.append([InlineKeyboardButton(
                text=f"✅ Выдать: {name}",
                callback_data=f"afind_grant:{tg_id}:{pid}",
            )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_list_kb(offset: int, total: int, page_size: int = PAGE_SIZE) -> InlineKeyboardMarkup:
    """Prev / Next navigation for paginated /admin_list.

    Only renders buttons that make sense (no Back on first page, no Forward past end).
    """
    row = []
    if offset > 0:
        prev_offset = max(0, offset - page_size)
        row.append(InlineKeyboardButton(
            text=f"← {prev_offset}–{offset - 1}",
            callback_data=f"alist:{prev_offset}",
        ))
    next_offset = offset + page_size
    if next_offset < total:
        end = min(next_offset + page_size - 1, total - 1)
        row.append(InlineKeyboardButton(
            text=f"→ {next_offset}–{end}",
            callback_data=f"alist:{next_offset}",
        ))
    return InlineKeyboardMarkup(inline_keyboard=[row] if row else [])


# ── text formatters ────────────────────────────────────────────────────────────

def format_list_page(subs: list[dict], offset: int, total: int) -> str:
    """Render one page of /admin_list as HTML text."""
    page_num = offset // PAGE_SIZE + 1
    lines = [f"<b>Активные подписки ({total}), стр. {page_num}:</b>\n"]
    for s in subs:
        until = s["active_until"][:10] if s.get("active_until") else "—"
        name_part = f"@{s['username']}" if s.get("username") else f"id:{s['telegram_id']}"
        lines.append(f"• {name_part} | {s['product_id']} | до {until}")
    return "\n".join(lines)


def format_user_card(user: dict) -> str:
    """Render /admin_find user card as HTML text."""
    first_name = user.get("first_name") or "—"
    username_part = f"@{user['username']}" if user.get("username") else f"ID: {user['telegram_id']}"
    first_seen = (user.get("first_seen") or "")[:10]
    last_seen = (user.get("last_seen") or "")[:10]
    lines = [
        f"👤 {username_part}",
        f"Имя: {first_name}",
        f"Первый визит: {first_seen} · Последний: {last_seen}",
        "",
        "<b>Подписки:</b>",
    ]
    if user.get("subscriptions"):
        for s in user["subscriptions"]:
            until = s["active_until"][:10] if s.get("active_until") else "—"
            icon = "✅" if s["status"] == "active" else "❌"
            lines.append(f"  {icon} {s['name']} — {s['status']} до {until}")
    else:
        lines.append("  нет подписок")
    return "\n".join(lines)
