"""Клиентский контур: /start, каталог продуктов, кнопки оплаты и ссылок."""

import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import settings
from db import repo
from services import channels
from services.prodamus import build_payment_url

logger = logging.getLogger(__name__)

_STATUS_LABEL = {
    "active": "✅ активна",
    "pending": "⏳ ожидает оплаты",
    "expired": "❌ истекла",
    "cancelled": "❌ отменена",
}


def register_client_handlers(dp: Dispatcher) -> None:
    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(cb_buy, F.data.startswith("buy:"))
    dp.callback_query.register(cb_relink, F.data.startswith("relink:"))


async def cmd_start(msg: Message) -> None:
    await repo.upsert_user(
        msg.from_user.id,
        msg.from_user.username,
        msg.from_user.first_name,
        settings.DB_PATH,
    )

    products = await repo.get_all_products(settings.DB_PATH)
    subs = await repo.get_subscriptions(msg.from_user.id, settings.DB_PATH)
    sub_map = {s["product_id"]: s for s in subs}

    if not products:
        await msg.answer("Каналы пока не настроены. Загляни позже!")
        return

    lines = ["<b>Наши закрытые каналы:</b>\n"]
    buttons: list[list[InlineKeyboardButton]] = []

    for p in products:
        sub = sub_map.get(p["product_id"])
        status = sub["status"] if sub else None
        label = _STATUS_LABEL.get(status, "")
        desc = f" — {p['description']}" if p.get("description") else ""
        lines.append(f"• <b>{p['name']}</b>{desc}\n  {p['price']} ₽/мес {label}")

        if status == "active":
            buttons.append([InlineKeyboardButton(
                text=f"🔗 {p['name']} — получить ссылку",
                callback_data=f"relink:{p['product_id']}",
            )])
        else:
            verb = "🔄 Оформить снова" if status in ("expired", "cancelled") else "💳 Купить"
            buttons.append([InlineKeyboardButton(
                text=f"{verb} — {p['name']}",
                callback_data=f"buy:{p['product_id']}",
            )])

    await msg.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


async def cb_buy(call: CallbackQuery, bot: Bot) -> None:
    product_id = call.data.split(":", 1)[1]
    product = await repo.get_product(product_id, settings.DB_PATH)

    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return

    await repo.upsert_subscription(
        telegram_id=call.from_user.id,
        product_id=product_id,
        status="pending",
        db_path=settings.DB_PATH,
    )

    url = build_payment_url(
        tg_id=call.from_user.id,
        product=product,
        webhook_base_url=settings.WEBHOOK_BASE_URL,
        secret=settings.PRODAMUS_SECRET,
    )

    await call.message.answer(
        f"💳 <b>{product['name']}</b>\n\n"
        f"Стоимость: {product['price']} ₽/месяц\n\n"
        "Нажми кнопку — Prodamus откроет форму оплаты.\n"
        "После оплаты ты получишь ссылку в этот чат автоматически.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="💳 Перейти к оплате", url=url),
        ]]),
    )
    await call.answer()


async def cb_relink(call: CallbackQuery, bot: Bot) -> None:
    product_id = call.data.split(":", 1)[1]
    product = await repo.get_product(product_id, settings.DB_PATH)
    sub = await repo.get_subscription(call.from_user.id, product_id, settings.DB_PATH)

    if not sub or sub["status"] != "active":
        await call.answer("Подписка неактивна", show_alert=True)
        return

    try:
        channel_link, discussion_link = await channels.grant_access(bot, call.from_user.id, product)
    except Exception as e:
        logger.error("grant_access failed: %s", e)
        await call.answer("Не удалось создать ссылку. Попробуй позже.", show_alert=True)
        return

    await call.message.answer(
        f"🔗 <b>Ссылки для «{product['name']}»</b>\n\n"
        f"Канал: {channel_link}\n"
        f"Беседа: {discussion_link}\n\n"
        "<i>Ссылки одноразовые и действуют 7 дней.</i>",
        parse_mode="HTML",
    )
    await call.answer()
