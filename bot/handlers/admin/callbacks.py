"""Admin callback query handlers."""

import logging
from datetime import datetime

from aiogram import Dispatcher, F
from aiogram.types import CallbackQuery, Message as TgMessage

from app.context import AppContext
from app import admin as app_admin
from app import subscriptions
from config import settings
from ui import keyboards, messages

logger = logging.getLogger(__name__)


def _msg(call: CallbackQuery) -> TgMessage:
    """Narrow call.message to Message; always accessible in our admin callbacks."""
    assert isinstance(call.message, TgMessage)
    return call.message


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


# ── payment notification callbacks ────────────────────────────────────────────


async def cb_apay_grant(call: CallbackQuery, app: AppContext) -> None:
    assert call.data is not None
    _, tg_id_str, product_id = call.data.split(":", 2)
    try:
        await subscriptions.grant(app, int(tg_id_str), product_id, order_id="manual")
    except ValueError as e:
        await call.answer(str(e), show_alert=True)
        return
    ts = datetime.now().strftime("%d.%m.%Y %H:%M")
    msg = _msg(call)
    await msg.edit_text(
        msg.html_text + f"\n\n✅ Доступ выдан вручную {ts}",
        parse_mode="HTML",
        reply_markup=None,
    )
    await call.answer("Доступ выдан")


async def cb_apay_revoke(call: CallbackQuery) -> None:
    """First step: show confirmation keyboard before revoking."""
    assert call.data is not None
    _, tg_id_str, product_id = call.data.split(":", 2)
    await _msg(call).edit_reply_markup(
        reply_markup=keyboards.payment_revoke_confirm_kb(int(tg_id_str), product_id)
    )
    await call.answer()


async def cb_apay_revoke_confirm(call: CallbackQuery, app: AppContext) -> None:
    """Second step: actually revoke after confirmation."""
    assert call.data is not None
    _, tg_id_str, product_id = call.data.split(":", 2)
    try:
        await subscriptions.revoke(app, int(tg_id_str), product_id, notify_user=False)
    except ValueError as e:
        await call.answer(str(e), show_alert=True)
        return
    ts = datetime.now().strftime("%d.%m.%Y %H:%M")
    msg = _msg(call)
    await msg.edit_text(
        msg.html_text + f"\n\n❌ Доступ отозван вручную {ts}",
        parse_mode="HTML",
        reply_markup=None,
    )
    await call.answer("Доступ отозван")


async def cb_apay_revoke_cancel(call: CallbackQuery) -> None:
    """Restore original grant/revoke keyboard after cancelling revoke."""
    assert call.data is not None
    _, tg_id_str, product_id = call.data.split(":", 2)
    await _msg(call).edit_reply_markup(
        reply_markup=keyboards.payment_notification_kb(int(tg_id_str), product_id)
    )
    await call.answer("Отменено")


# ── user card callbacks (/admin_find) ─────────────────────────────────────────


async def cb_afind_grant(call: CallbackQuery, app: AppContext) -> None:
    assert call.data is not None
    _, tg_id_str, product_id = call.data.split(":", 2)
    try:
        await subscriptions.grant(app, int(tg_id_str), product_id, order_id="manual")
    except ValueError as e:
        await call.answer(str(e), show_alert=True)
        return
    await _refresh_user_card(call, app, int(tg_id_str))


async def cb_afind_revoke(call: CallbackQuery, app: AppContext) -> None:
    assert call.data is not None
    _, tg_id_str, product_id = call.data.split(":", 2)
    try:
        await subscriptions.revoke(app, int(tg_id_str), product_id, notify_user=True)
    except ValueError as e:
        await call.answer(str(e), show_alert=True)
        return
    await _refresh_user_card(call, app, int(tg_id_str))


async def _refresh_user_card(call: CallbackQuery, app: AppContext, tg_id: int) -> None:
    user = await app_admin.find_user(app, str(tg_id))
    if not user:
        await call.answer("Готово")
        return
    products = await app_admin.get_products(app)
    await _msg(call).edit_text(
        messages.format_user_card(user),
        parse_mode="HTML",
        reply_markup=keyboards.user_card_kb(tg_id, user["subscriptions"], products),
    )
    await call.answer("Готово")


# ── user card open callbacks ───────────────────────────────────────────────────


async def _send_user_card(call: CallbackQuery, app: AppContext, tg_id: int) -> None:
    user = await app_admin.find_user(app, str(tg_id))
    if not user:
        await call.answer("Пользователь не найден", show_alert=True)
        return
    products = await app_admin.get_products(app)
    await _msg(call).answer(
        messages.format_user_card(user),
        parse_mode="HTML",
        reply_markup=keyboards.user_card_kb(tg_id, user["subscriptions"], products),
    )
    await call.answer()


async def cb_alist_user(call: CallbackQuery, app: AppContext) -> None:
    assert call.data is not None
    await _send_user_card(call, app, int(call.data.split(":", 1)[1]))


async def cb_aexp_find(call: CallbackQuery, app: AppContext) -> None:
    assert call.data is not None
    await _send_user_card(call, app, int(call.data.split(":", 1)[1]))


# ── pagination callback (/admin_list) ─────────────────────────────────────────


async def cb_alist(call: CallbackQuery, app: AppContext) -> None:
    assert call.data is not None
    offset = int(call.data.split(":", 1)[1])
    subs = await app_admin.list_subscriptions(app)
    total = len(subs)
    page = subs[offset : offset + keyboards.PAGE_SIZE]
    if not page:
        await call.answer("Нет данных", show_alert=True)
        return
    await _msg(call).edit_text(
        messages.format_list_page(page, offset=offset, total=total),
        parse_mode="HTML",
        reply_markup=keyboards.admin_list_kb(offset=offset, total=total, page=page),
    )
    await call.answer()
