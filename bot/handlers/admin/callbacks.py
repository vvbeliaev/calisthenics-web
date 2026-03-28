"""Admin callback query handlers and payment notification.

notify_admin is called from webhooks/prodamus.py after a successful payment.
All cb_* functions handle inline keyboard button presses.
"""

import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import CallbackQuery

from config import settings
from db import repo
from handlers.admin.keyboards import (
    PAGE_SIZE,
    admin_list_kb,
    expiring_kb,
    format_list_page,
    format_user_card,
    payment_notification_kb,
    payment_revoke_confirm_kb,
    user_card_kb,
)
from services import channels

logger = logging.getLogger(__name__)


def register_admin_callbacks(dp: Dispatcher) -> None:
    _admin = F.from_user.id == settings.ADMIN_ID
    dp.callback_query.register(cb_apay_grant, _admin, F.data.startswith("apay_grant:"))
    dp.callback_query.register(
        cb_apay_revoke_confirm, _admin, F.data.startswith("apay_revoke_confirm:")
    )
    dp.callback_query.register(
        cb_apay_revoke_cancel, _admin, F.data.startswith("apay_revoke_cancel:")
    )
    dp.callback_query.register(
        cb_apay_revoke, _admin, F.data.startswith("apay_revoke:")
    )
    dp.callback_query.register(
        cb_afind_grant, _admin, F.data.startswith("afind_grant:")
    )
    dp.callback_query.register(
        cb_afind_revoke, _admin, F.data.startswith("afind_revoke:")
    )
    dp.callback_query.register(cb_alist_user, _admin, F.data.startswith("alist_user:"))
    dp.callback_query.register(cb_alist, _admin, F.data.startswith("alist:"))
    dp.callback_query.register(cb_aexp_find, _admin, F.data.startswith("aexp_find:"))


# ── payment notification ───────────────────────────────────────────────────────


async def notify_admin(
    bot: Bot, tg_id: int, product: dict, amount: str, order_id: str
) -> None:
    """Send payment notification to admin with grant/revoke action buttons."""
    username_info = ""
    try:
        chat = await bot.get_chat(tg_id)
        username_info = f"@{chat.username} " if chat.username else ""
    except Exception:
        pass

    await bot.send_message(
        settings.ADMIN_ID,
        f"💰 <b>Новая оплата!</b>\n\n"
        f"Пользователь: {username_info}(tg_id: {tg_id})\n"
        f"Продукт: {product['name']}\n"
        f"Сумма: {amount} ₽\n"
        f"Order ID: {order_id}",
        parse_mode="HTML",
        reply_markup=payment_notification_kb(tg_id, product["product_id"]),
    )


# ── payment notification callbacks ────────────────────────────────────────────


async def cb_apay_grant(call: CallbackQuery, bot: Bot) -> None:
    _, tg_id_str, product_id = call.data.split(":", 2)
    tg_id = int(tg_id_str)
    product = await repo.get_product(product_id, settings.DB_PATH)
    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return
    await repo.activate_subscription(
        tg_id, product_id, order_id="manual", db_path=settings.DB_PATH
    )
    channel_link, discussion_link = await channels.grant_access(bot, tg_id, product)
    try:
        await bot.send_message(
            tg_id,
            f"✅ <b>Доступ к «{product['name']}» открыт!</b>\n\n"
            f"Канал: {channel_link}\nБеседа: {discussion_link}\n\n"
            "<i>Ссылки одноразовые, действуют 7 дней.</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning("Не удалось уведомить пользователя %s: %s", tg_id, e)
    ts = datetime.now().strftime("%d.%m.%Y %H:%M")
    await call.message.edit_text(
        call.message.html_text + f"\n\n✅ Доступ выдан вручную {ts}",
        parse_mode="HTML",
        reply_markup=None,
    )
    await call.answer("Доступ выдан")


async def cb_apay_revoke(call: CallbackQuery) -> None:
    """First step: show confirmation keyboard before revoking."""
    _, tg_id_str, product_id = call.data.split(":", 2)
    await call.message.edit_reply_markup(
        reply_markup=payment_revoke_confirm_kb(int(tg_id_str), product_id)
    )
    await call.answer()


async def cb_apay_revoke_confirm(call: CallbackQuery, bot: Bot) -> None:
    """Second step: actually revoke after confirmation."""
    _, tg_id_str, product_id = call.data.split(":", 2)
    tg_id = int(tg_id_str)
    product = await repo.get_product(product_id, settings.DB_PATH)
    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return
    await repo.set_subscription_status(tg_id, product_id, "cancelled", settings.DB_PATH)
    await channels.revoke_access(bot, tg_id, product)
    ts = datetime.now().strftime("%d.%m.%Y %H:%M")
    await call.message.edit_text(
        call.message.html_text + f"\n\n❌ Доступ отозван вручную {ts}",
        parse_mode="HTML",
        reply_markup=None,
    )
    await call.answer("Доступ отозван")


async def cb_apay_revoke_cancel(call: CallbackQuery) -> None:
    """Restore original grant/revoke keyboard after cancelling revoke."""
    _, tg_id_str, product_id = call.data.split(":", 2)
    await call.message.edit_reply_markup(
        reply_markup=payment_notification_kb(int(tg_id_str), product_id)
    )
    await call.answer("Отменено")


# ── user card callbacks (/admin_find) ─────────────────────────────────────────


async def cb_afind_grant(call: CallbackQuery, bot: Bot) -> None:
    _, tg_id_str, product_id = call.data.split(":", 2)
    tg_id = int(tg_id_str)
    product = await repo.get_product(product_id, settings.DB_PATH)
    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return
    await repo.activate_subscription(
        tg_id, product_id, order_id="manual", db_path=settings.DB_PATH
    )
    channel_link, discussion_link = await channels.grant_access(bot, tg_id, product)
    try:
        await bot.send_message(
            tg_id,
            f"✅ <b>Доступ к «{product['name']}» открыт!</b>\n\n"
            f"Канал: {channel_link}\nБеседа: {discussion_link}\n\n"
            "<i>Ссылки одноразовые, действуют 7 дней.</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning("Не удалось уведомить пользователя %s: %s", tg_id, e)
    await _refresh_user_card(call, tg_id)


async def cb_afind_revoke(call: CallbackQuery, bot: Bot) -> None:
    _, tg_id_str, product_id = call.data.split(":", 2)
    tg_id = int(tg_id_str)
    product = await repo.get_product(product_id, settings.DB_PATH)
    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return
    await repo.set_subscription_status(tg_id, product_id, "cancelled", settings.DB_PATH)
    await channels.revoke_access(bot, tg_id, product)
    try:
        await bot.send_message(
            tg_id, "❌ Ваш доступ к каналу был отозван администратором."
        )
    except Exception as e:
        logger.warning("Не удалось уведомить пользователя %s: %s", tg_id, e)
    await _refresh_user_card(call, tg_id)


async def _refresh_user_card(call: CallbackQuery, tg_id: int) -> None:
    """Re-render and edit the user card message after a grant/revoke action."""
    user = await repo.find_user(settings.DB_PATH, str(tg_id))
    all_products = await repo.get_all_products(settings.DB_PATH)
    if not user:
        await call.answer("Готово")
        return
    text = format_user_card(user)
    kb = user_card_kb(tg_id, user["subscriptions"], all_products)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer("Готово")


# ── user card open callbacks (/admin_list row click, /admin_expiring find) ────


async def _send_user_card(call: CallbackQuery, tg_id: int) -> None:
    """Fetch user data and send a new user card message."""
    user = await repo.find_user(settings.DB_PATH, str(tg_id))
    if not user:
        await call.answer("Пользователь не найден", show_alert=True)
        return
    all_products = await repo.get_all_products(settings.DB_PATH)
    text = format_user_card(user)
    kb = user_card_kb(tg_id, user["subscriptions"], all_products)
    await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


async def cb_alist_user(call: CallbackQuery) -> None:
    tg_id = int(call.data.split(":", 1)[1])
    await _send_user_card(call, tg_id)


async def cb_aexp_find(call: CallbackQuery) -> None:
    tg_id = int(call.data.split(":", 1)[1])
    await _send_user_card(call, tg_id)


# ── pagination callback (/admin_list) ─────────────────────────────────────────


async def cb_alist(call: CallbackQuery) -> None:
    offset = int(call.data.split(":", 1)[1])
    subs = await repo.get_active_subscriptions(settings.DB_PATH)
    total = len(subs)
    page = subs[offset : offset + PAGE_SIZE]
    if not page:
        await call.answer("Нет данных", show_alert=True)
        return
    text = format_list_page(page, offset=offset, total=total)
    kb = admin_list_kb(offset=offset, total=total, page=page)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()
