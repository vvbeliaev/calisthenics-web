"""Admin command handlers."""

import logging
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.context import AppContext
from app import admin as app_admin
from app import subscriptions
from config import settings
from ui import keyboards, messages

_USER_ID_RE = re.compile(r"#id(\d+)")
logger = logging.getLogger(__name__)


def register_admin_commands(dp: Dispatcher) -> None:
    _admin = F.from_user.id == settings.ADMIN_ID
    dp.message.register(admin_grant, Command("admin_grant"))
    dp.message.register(admin_revoke, Command("admin_revoke"))
    dp.message.register(admin_list, Command("admin_list"))
    dp.message.register(admin_stats, Command("admin_stats"))
    dp.message.register(admin_find, Command("admin_find"))
    dp.message.register(admin_expiring, Command("admin_expiring"))
    dp.message.register(admin_stats, _admin, F.text == keyboards.BTN_STATS)
    dp.message.register(admin_list, _admin, F.text == keyboards.BTN_LIST)
    dp.message.register(admin_expiring, _admin, F.text == keyboards.BTN_EXPIRING)
    dp.message.register(admin_find_prompt, _admin, F.text == keyboards.BTN_FIND)
    dp.message.register(
        admin_reply_to_user,
        _admin,
        F.reply_to_message,
        F.text,
        ~F.text.startswith("/"),
    )


def _is_admin(msg: Message) -> bool:
    return msg.from_user is not None and msg.from_user.id == settings.ADMIN_ID


async def admin_grant(msg: Message, app: AppContext) -> None:
    if not _is_admin(msg):
        return
    assert msg.text is not None
    parts = msg.text.split()
    if len(parts) < 3 or len(parts) > 4:
        await msg.answer("Использование: /admin_grant {tg_id} {product_id} [days]")
        return
    tg_id = int(parts[1])
    product_id = parts[2]
    days = int(parts[3]) if len(parts) == 4 and parts[3].isdigit() else 30
    try:
        await subscriptions.grant(app, tg_id, product_id, order_id="manual", days=days)
        await msg.answer(f"✅ Доступ выдан: tg_id={tg_id} продукт={product_id} дней={days}")
    except ValueError as e:
        await msg.answer(str(e))
    except Exception as e:
        logger.error("admin_grant failed: %s", e)
        await msg.answer(f"❌ Ошибка: {e}")


async def admin_revoke(msg: Message, app: AppContext) -> None:
    if not _is_admin(msg):
        return
    assert msg.text is not None
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.answer("Использование: /admin_revoke {tg_id} {product_id}")
        return
    tg_id = int(parts[1])
    product_id = parts[2]
    try:
        await subscriptions.revoke(app, tg_id, product_id, notify_user=True)
        await msg.answer(f"✅ Доступ отозван: tg_id={tg_id} продукт={product_id}")
    except ValueError as e:
        await msg.answer(str(e))
    except Exception as e:
        logger.error("admin_revoke failed: %s", e)
        await msg.answer(f"❌ Ошибка: {e}")


async def admin_list(msg: Message, app: AppContext) -> None:
    if not _is_admin(msg):
        return
    subs = await app_admin.list_subscriptions(app)
    if not subs:
        await msg.answer("Нет активных подписчиков.")
        return
    total = len(subs)
    page = subs[:keyboards.PAGE_SIZE]
    await msg.answer(
        messages.format_list_page(page, offset=0, total=total),
        parse_mode="HTML",
        reply_markup=keyboards.admin_list_kb(offset=0, total=total, page=page),
    )


async def admin_reply_to_user(msg: Message, bot: Bot) -> None:
    assert msg.reply_to_message is not None
    original_text = msg.reply_to_message.text or ""
    match = _USER_ID_RE.search(original_text)
    if not match:
        await msg.answer("⚠️ Не найден #id — не могу определить получателя.")
        return
    target_id = int(match.group(1))
    try:
        await bot.send_message(
            target_id,
            f"📩 <b>Ответ от тренера:</b>\n\n{msg.html_text}",
            parse_mode="HTML",
        )
        await msg.answer(f"✅ Доставлено пользователю {target_id}")
    except Exception as e:
        logger.error("Не удалось доставить ответ пользователю %s: %s", target_id, e)
        await msg.answer(f"❌ Ошибка доставки: {e}")


async def admin_stats(msg: Message, app: AppContext) -> None:
    if not _is_admin(msg):
        return
    stats = await app_admin.get_stats(app)
    await msg.answer(messages.format_stats(stats), parse_mode="HTML")


async def admin_find(msg: Message, app: AppContext) -> None:
    if not _is_admin(msg):
        return
    assert msg.text is not None
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: /admin_find @username или /admin_find tg_id")
        return
    user = await app_admin.find_user(app, parts[1].strip())
    if not user:
        await msg.answer(f"Пользователь «{parts[1].strip()}» не найден.")
        return
    products = await app_admin.get_products(app)
    await msg.answer(
        messages.format_user_card(user),
        parse_mode="HTML",
        reply_markup=keyboards.user_card_kb(user["telegram_id"], user["subscriptions"], products),
    )


async def admin_find_prompt(msg: Message) -> None:
    await msg.answer("Введи /admin_find @username или /admin_find tg_id")


async def admin_expiring(msg: Message, app: AppContext) -> None:
    if not _is_admin(msg):
        return
    assert msg.text is not None
    parts = msg.text.split()
    days = 3
    if len(parts) == 2 and parts[1].isdigit():
        days = min(int(parts[1]), 30)
    subs = await app_admin.list_expiring(app, days)
    if not subs:
        await msg.answer(f"Нет истекающих подписок за {days} дней.")
        return
    await msg.answer(
        messages.format_expiring(subs, days),
        parse_mode="HTML",
        reply_markup=keyboards.expiring_kb(subs),
    )
