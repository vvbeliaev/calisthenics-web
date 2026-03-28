"""Клиентский контур: /start, кнопки оплаты и ссылок."""

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

WELCOME_TEXT = (
    "💥 <b>Добро пожаловать в Calisthenics 1.0 BAZA (второй поток)!</b>\n"
    "Ты только что сделал первый шаг к сильному, гибкому и прокачанному телу "
    "— без тренажёров и спортзалов, только с весом своего тела 💪\n\n"
    "📌 <b>Что тебя ждёт:</b>\n"
    "— Более 120 упражнений калистеники\n"
    "— Программы с 4 уровнями сложности\n"
    "— Пошаговый прогресс от базовых движений до элементов силы\n"
    "— Поддержка от Евгения Семеняка и сообщества единомышленников\n"
    "— Всё, что нужно: 4 тренировки в неделю по 30–60 мин\n\n"
    "Действуй. Сила, красота и контроль над телом — это не мечта, а практика.\n"
    "<i>С уважением, Евгений Семеняка</i>"
)


def register_client_handlers(dp: Dispatcher) -> None:
    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(cb_relink, F.data.startswith("relink:"))
    dp.callback_query.register(cb_test_grant, F.data.startswith("test_grant:"))
    # Catch-all: любое текстовое сообщение не от админа и не команда
    dp.message.register(
        user_message_to_admin,
        F.text,
        ~F.text.startswith("/"),
        F.from_user.id != settings.ADMIN_ID,
    )


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

    # Строим кнопки: активным — "получить ссылку", остальным — прямой URL Prodamus
    buttons: list[list[InlineKeyboardButton]] = []

    for p in products:
        sub = sub_map.get(p["product_id"])
        status = sub["status"] if sub else None

        if status == "active":
            buttons.append([InlineKeyboardButton(
                text=f"🔗 Получить ссылку — {p['name']}",
                callback_data=f"relink:{p['product_id']}",
            )])
        elif settings.TEST_MODE:
            # Тестовый режим: показываем кнопку, подписка выдаётся только при клике
            buttons.append([InlineKeyboardButton(
                text=f"🧪 Тест — {p['name']}",
                callback_data=f"test_grant:{p['product_id']}",
            )])
        else:
            pay_url = build_payment_url(
                tg_id=msg.from_user.id,
                product=p,
                webhook_base_url=settings.WEBHOOK_BASE_URL,
                secret=settings.PRODAMUS_SECRET,
            )
            verb = "🔄" if status in ("expired", "cancelled") else "💳"
            buttons.append([InlineKeyboardButton(
                text=f"{verb} Оформить подписку — {p['name']} ({p['price']} ₽/мес)",
                url=pay_url,
            )])

    if not products:
        await msg.answer("Каналы пока не настроены. Загляни позже!")
        return

    if settings.WELCOME_PHOTO:
        await msg.answer_photo(
            photo=settings.WELCOME_PHOTO,
            caption=WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
    else:
        await msg.answer(
            WELCOME_TEXT,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


async def user_message_to_admin(msg: Message, bot: Bot) -> None:
    """Пересылает текстовое сообщение пользователя админу."""
    user = msg.from_user
    name = user.full_name or "Неизвестный"
    username_part = f"@{user.username}" if user.username else "без @"

    await bot.send_message(
        settings.ADMIN_ID,
        f"💬 {name} ({username_part}) #id{user.id}\n"
        f"{'─' * 20}\n"
        f"{msg.text}",
    )
    await msg.answer("✉️ Сообщение отправлено тренеру. Ожидайте ответа.")


async def cb_test_grant(call: CallbackQuery, bot: Bot) -> None:
    """TEST_MODE: выдаёт активную подписку и сразу возвращает ссылки."""
    product_id = call.data.split(":", 1)[1]
    product = await repo.get_product(product_id, settings.DB_PATH)

    if not product:
        await call.answer("Продукт не найден", show_alert=True)
        return

    await repo.upsert_subscription(
        telegram_id=call.from_user.id,
        product_id=product_id,
        status="active",
        db_path=settings.DB_PATH,
    )
    logger.info("TEST_MODE: granted subscription %s to user %s", product_id, call.from_user.id)

    try:
        channel_link, discussion_link = await channels.grant_access(bot, call.from_user.id, product)
    except Exception as e:
        logger.error("TEST_MODE grant_access failed: %s", e)
        await call.answer(f"Ошибка создания ссылки: {e}", show_alert=True)
        return

    await call.message.answer(
        f"🧪 <b>TEST MODE — «{product['name']}»</b>\n\n"
        f"Канал: {channel_link}\n"
        f"Беседа: {discussion_link}\n\n"
        "<i>Ссылки одноразовые, действуют 7 дней. Кликни чтобы вступить.</i>",
        parse_mode="HTML",
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
