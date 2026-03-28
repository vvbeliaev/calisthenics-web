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


def admin_list_kb(
    offset: int,
    total: int,
    page: list[dict],
    page_size: int = PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """User row buttons + Prev/Next navigation for /admin_list.

    Each user row is a clickable button that opens the user card.
    Navigation shows page numbers instead of raw offsets.
    """
    rows = []

    for s in page:
        until = s["active_until"][:10] if s.get("active_until") else "—"
        label = f"@{s['username']}" if s.get("username") else f"ID:{s['telegram_id']}"
        rows.append([InlineKeyboardButton(
            text=f"{label} · {s['product_id']} · до {until}",
            callback_data=f"alist_user:{s['telegram_id']}",
        )])

    nav = []
    if offset > 0:
        prev_offset = max(0, offset - page_size)
        prev_page = prev_offset // page_size + 1
        nav.append(InlineKeyboardButton(
            text=f"← Стр. {prev_page}",
            callback_data=f"alist:{prev_offset}",
        ))
    next_offset = offset + page_size
    if next_offset < total:
        next_page = next_offset // page_size + 1
        nav.append(InlineKeyboardButton(
            text=f"→ Стр. {next_page}",
            callback_data=f"alist:{next_offset}",
        ))
    if nav:
        rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def expiring_kb(subs: list[dict]) -> InlineKeyboardMarkup | None:
    """One 'Find' button per user in /admin_expiring output."""
    rows = []
    for s in subs:
        label = f"@{s['username']}" if s.get("username") else f"ID:{s['telegram_id']}"
        rows.append([InlineKeyboardButton(
            text=f"🔍 {label}",
            callback_data=f"aexp_find:{s['telegram_id']}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


# ── text formatters ────────────────────────────────────────────────────────────

def format_list_page(subs: list[dict], offset: int, total: int) -> str:
    """Render /admin_list header. User rows are rendered as keyboard buttons."""
    page_num = offset // PAGE_SIZE + 1
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    return f"<b>Активные подписки ({total}), стр. {page_num}/{total_pages}:</b>"


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
