"""Telegram message text formatters.

All functions are pure — no I/O, no bot calls, no settings access.
"""

from datetime import datetime

from ui.keyboards import PAGE_SIZE


WELCOME_TEXT = (
    "💥 <b>Добро пожаловать в Calisthenics 1.0 BAZA</b>\n\n"
    "Ты только что сделал первый шаг к сильному, гибкому и прокачанному телу "
    "— без тренажёров и спортзалов, только с весом своего тела 💪\n\n"
    "📌 <b>Что тебя ждёт:</b>\n"
    "— Более 130+ упражнений калистеники\n"
    "— Программы с 4 уровнями сложности\n"
    "— Пошаговый прогресс от базовых движений до элементов силы\n"
    "— Поддержка от Евгения Семеняка и сообщества единомышленников\n"
    "— Всё, что нужно: 3-4 тренировки в неделю по 30–60 мин\n\n"
    "Действуй. Сила, красота и контроль над телом — это не мечта, а практика.\n"
    "<i>С уважением, Евгений Семеняка</i>"
)


# ── subscription notifications ─────────────────────────────────────────────────


def format_access_granted(product_name: str, channel_link: str, discussion_link: str) -> str:
    return (
        f"✅ <b>Доступ к «{product_name}» открыт!</b>\n\n"
        f"Канал: {channel_link}\nБеседа: {discussion_link}\n\n"
        "<i>Ссылки одноразовые, действуют 7 дней.</i>"
    )


def format_access_revoked() -> str:
    return "❌ Ваш доступ к каналу был отозван администратором."


def format_subscription_expired(product_name: str) -> str:
    return (
        f"⏰ <b>Подписка на «{product_name}» истекла.</b>\n\n"
        "Нажми /start чтобы оформить снова."
    )


def format_relink(product_name: str, channel_link: str, discussion_link: str) -> str:
    return (
        f"🔗 <b>Ссылки для «{product_name}»</b>\n\n"
        f"Канал: {channel_link}\nБеседа: {discussion_link}\n\n"
        "<i>Ссылки одноразовые и действуют 7 дней.</i>"
    )


def format_test_grant(product_name: str, channel_link: str, discussion_link: str) -> str:
    return (
        f"🧪 <b>TEST MODE — «{product_name}»</b>\n\n"
        f"Канал: {channel_link}\nБеседа: {discussion_link}\n\n"
        "<i>Ссылки одноразовые, действуют 7 дней. Кликни чтобы вступить.</i>"
    )


# ── payment notifications ──────────────────────────────────────────────────────


def format_payment_success(product_name: str, channel_link: str, discussion_link: str) -> str:
    return (
        f"🎉 <b>Оплата прошла!</b>\n\n"
        f"Добро пожаловать в «{product_name}»!\n\n"
        f"Канал: {channel_link}\nБеседа: {discussion_link}\n\n"
        "<i>Ссылки одноразовые, действуют 7 дней.\n"
        "Если понадобятся снова — нажми /start.</i>"
    )


def format_payment_failed() -> str:
    return (
        "❌ <b>Оплата не прошла.</b>\n\n"
        "Подписка отменена. Нажми /start чтобы оформить снова."
    )


def format_subscription_renewed(product_name: str) -> str:
    return (
        f"🔄 <b>Подписка на «{product_name}» продлена!</b>\n\n"
        "Оплата прошла автоматически. Доступ продолжает действовать."
    )


def format_subscription_deactivated(product_name: str) -> str:
    return (
        f"⛔ <b>Подписка на «{product_name}» деактивирована.</b>\n\n"
        "Доступ к каналу закрыт. Нажми /start чтобы оформить снова."
    )


def format_payment_notification(
    username_info: str,
    tg_id: int,
    product_name: str,
    amount: str,
    order_id: str,
    label: str = "Payment",
) -> str:
    return (
        f"💰 <b>{label}!</b>\n\n"
        f"Пользователь: {username_info}(tg_id: {tg_id})\n"
        f"Продукт: {product_name}\n"
        f"Сумма: {amount} ₽\n"
        f"Order ID: {order_id}"
    )


# ── admin text formatters ──────────────────────────────────────────────────────


def format_stats(stats: dict) -> str:
    today = datetime.now().strftime("%d.%m.%Y")
    return (
        f"📊 <b>Статистика на {today}</b>\n"
        "─────────────────────────\n"
        f"👥 Пользователей в боте:    {stats['total_users']}\n"
        f"✅ Активных подписок:       {stats['active']}\n"
        f"❌ Истекших / отменённых:   {stats['expired_cancelled']}\n"
        "─────────────────────────\n"
        f"⚠️  Истекают за 3 дня:        {stats['expiring_3d']}"
    )


def format_user_card(user: dict) -> str:
    first_name = user.get("first_name") or "—"
    username_part = (
        f"@{user['username']}" if user.get("username") else f"ID: {user['telegram_id']}"
    )
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


def format_list_page(subs: list[dict], offset: int, total: int) -> str:
    """Render active subscriptions list as text."""
    page_num = offset // PAGE_SIZE + 1
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    lines = [f"<b>Активные подписки ({total}), стр. {page_num}/{total_pages}:</b>"]
    for s in subs:
        until = s["active_until"][:10] if s.get("active_until") else "—"
        label = f"@{s['username']}" if s.get("username") else f"id:{s['telegram_id']}"
        lines.append(f"• {label} · {s['product_id']} · до {until}")
    return "\n".join(lines)


def format_expiring(subs: list[dict], days: int) -> str:
    lines = [f"⏰ <b>Истекают за {days} дней ({len(subs)}):</b>\n"]
    for s in subs:
        until = s["active_until"][:10] if s.get("active_until") else "—"
        user_part = (
            f"@{s['username']}" if s.get("username") else f"ID:{s['telegram_id']}"
        )
        lines.append(f"• {user_part} — {s['product_name']} — до {until}")
    return "\n".join(lines)
