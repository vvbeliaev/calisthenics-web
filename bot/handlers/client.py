"""Клиентский контур: /start, кнопки оплаты и ссылок."""

import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.context import AppContext
from app import admin as app_admin
from app import subscriptions
from config import settings
from ui import keyboards, messages

logger = logging.getLogger(__name__)


def _msg(call: CallbackQuery) -> Message:
    assert isinstance(call.message, Message)
    return call.message


def register_client_handlers(dp: Dispatcher) -> None:
    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(cb_relink, F.data.startswith("relink:"))
    dp.callback_query.register(cb_test_grant, F.data.startswith("test_grant:"))
    dp.message.register(
        user_message_to_admin,
        F.text,
        ~F.text.startswith("/"),
        F.from_user.id != settings.ADMIN_ID,
    )


async def cmd_start(msg: Message, app: AppContext) -> None:
    if msg.from_user is None:
        return
    await app_admin.upsert_user(app, msg.from_user.id, msg.from_user.username, msg.from_user.first_name)

    products = await app_admin.get_products(app)
    if not products:
        await msg.answer("Каналы пока не настроены. Загляни позже!")
        return

    subs = await subscriptions.get_user_subs(app, msg.from_user.id)
    sub_map = {s["product_id"]: s for s in subs}

    pay_urls: dict[str, str] = {}
    if not settings.TEST_MODE:
        from services.prodamus import build_payment_url
        import asyncio
        results = await asyncio.gather(
            *[
                build_payment_url(
                    tg_id=msg.from_user.id,
                    product=p,
                    webhook_base_url=settings.WEBHOOK_BASE_URL,
                    secret=settings.PRODAMUS_SECRET,
                )
                for p in products
                if sub_map.get(p["product_id"], {}).get("status") != "active"
            ],
            return_exceptions=True,
        )
        non_active = [
            p for p in products
            if sub_map.get(p["product_id"], {}).get("status") != "active"
        ]
        for p, result in zip(non_active, results):
            if isinstance(result, str):
                pay_urls[p["product_id"]] = result
            else:
                logger.warning("Failed to get payment URL for %s: %s", p["product_id"], result)

    kb = keyboards.start_kb(products, sub_map, settings.TEST_MODE, pay_urls)

    if msg.from_user.id == settings.ADMIN_ID:
        await msg.answer("🔧 Панель администратора", reply_markup=keyboards.admin_panel_kb())

    if settings.WELCOME_PHOTO:
        await msg.answer_photo(
            photo=settings.WELCOME_PHOTO,
            caption=messages.WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await msg.answer(messages.WELCOME_TEXT, parse_mode="HTML", reply_markup=kb)


async def user_message_to_admin(msg: Message, bot: Bot) -> None:
    """Пересылает текстовое сообщение пользователя админу."""
    if msg.from_user is None:
        return
    user = msg.from_user
    name = user.full_name or "Неизвестный"
    username_part = f"@{user.username}" if user.username else "без @"
    await bot.send_message(
        settings.ADMIN_ID,
        f"💬 {name} ({username_part}) #id{user.id}\n{'─' * 20}\n{msg.text}",
    )
    await msg.answer("✉️ Сообщение отправлено тренеру. Ожидайте ответа.")


async def cb_test_grant(call: CallbackQuery, app: AppContext) -> None:
    """TEST_MODE: выдаёт активную подписку и сразу возвращает ссылки."""
    assert call.data is not None
    product_id = call.data.split(":", 1)[1]
    product = await app_admin.get_product(app, product_id)
    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return
    try:
        channel_link, discussion_link = await subscriptions.grant_test(app, call.from_user.id, product_id)
    except Exception as e:
        logger.error("TEST_MODE grant_test failed: %s", e)
        await call.answer(f"Ошибка создания ссылки: {e}", show_alert=True)
        return
    await _msg(call).answer(
        messages.format_test_grant(product["name"], channel_link, discussion_link),
        parse_mode="HTML",
    )
    await call.answer()


async def cb_relink(call: CallbackQuery, app: AppContext) -> None:
    assert call.data is not None
    product_id = call.data.split(":", 1)[1]
    product = await app_admin.get_product(app, product_id)
    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return
    try:
        channel_link, discussion_link = await subscriptions.relink(app, call.from_user.id, product_id)
    except ValueError as e:
        await call.answer(str(e), show_alert=True)
        return
    except Exception as e:
        logger.error("relink failed: %s", e)
        await call.answer("Не удалось создать ссылку. Попробуй позже.", show_alert=True)
        return
    await _msg(call).answer(
        messages.format_relink(product["name"], channel_link, discussion_link),
        parse_mode="HTML",
    )
    await call.answer()
