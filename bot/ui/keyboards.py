"""Telegram keyboard builders.

All functions are pure — no I/O, no bot calls, no settings access.
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

PAGE_SIZE = 20

# Reply-keyboard button labels (used both to build the keyboard and to match incoming text)
BTN_STATS = "📊 Статистика"
BTN_LIST = "👥 Подписчики"
BTN_EXPIRING = "⏰ Истекают (3д)"
BTN_FIND = "🔍 Найти"


def admin_panel_kb() -> ReplyKeyboardMarkup:
    """Persistent reply keyboard shown to the admin at the bottom of the chat."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_LIST)],
            [KeyboardButton(text=BTN_EXPIRING), KeyboardButton(text=BTN_FIND)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Команда или /admin_find @username …",
    )


def start_kb(
    products: list[dict],
    sub_map: dict,
    test_mode: bool,
    pay_urls: dict[str, str],
) -> InlineKeyboardMarkup:
    """Build the /start catalog keyboard depending on subscription state.

    pay_urls: product_id → ready payment URL (pre-fetched by cmd_start).
    """
    buttons: list[list[InlineKeyboardButton]] = []
    for p in products:
        sub = sub_map.get(p["product_id"])
        status = sub["status"] if sub else None

        if status == "active":
            buttons.append([InlineKeyboardButton(
                text=f"🔗 Получить ссылку — {p['name']}",
                callback_data=f"relink:{p['product_id']}",
            )])
        elif test_mode:
            buttons.append([InlineKeyboardButton(
                text=f"🧪 Тест — {p['name']}",
                callback_data=f"test_grant:{p['product_id']}",
            )])
        else:
            pay_url = pay_urls.get(p["product_id"], "")
            verb = "🔄" if status in ("expired", "cancelled") else "💳"
            buttons.append([InlineKeyboardButton(
                text=f"{verb} Оформить подписку — {p['name']} ({p['price']} ₽/мес)",
                url=pay_url,
            )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_notification_kb(tg_id: int, product_id: str) -> InlineKeyboardMarkup:
    """Attached to the admin payment notification message."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выдать доступ",
                    callback_data=f"apay_grant:{tg_id}:{product_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отозвать",
                    callback_data=f"apay_revoke:{tg_id}:{product_id}",
                ),
            ]
        ]
    )


def payment_revoke_confirm_kb(tg_id: int, product_id: str) -> InlineKeyboardMarkup:
    """Two-step confirmation before revoking a just-paid subscription."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, отозвать",
                    callback_data=f"apay_revoke_confirm:{tg_id}:{product_id}",
                ),
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=f"apay_revoke_cancel:{tg_id}:{product_id}",
                ),
            ]
        ]
    )


def user_card_kb(
    tg_id: int,
    subscriptions: list[dict],
    all_products: list[dict],
) -> InlineKeyboardMarkup:
    """Per-product action buttons on a user card.

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
    page: list[dict] | None = None,
    page_size: int = PAGE_SIZE,
) -> InlineKeyboardMarkup:
    """Pagination navigation for /admin_list. Optionally includes clickable user rows."""
    rows: list[list[InlineKeyboardButton]] = []

    if page:
        for s in page:
            until = s["active_until"][:10] if s.get("active_until") else "—"
            label = f"@{s['username']}" if s.get("username") else f"ID:{s['telegram_id']}"
            rows.append([InlineKeyboardButton(
                text=f"{label} · {s['product_id']} · до {until}",
                callback_data=f"alist_user:{s['telegram_id']}",
            )])

    nav: list[InlineKeyboardButton] = []
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
