"""Admin command handlers.

Existing: /admin_grant, /admin_revoke, /admin_list, reply forwarding.
New commands added in this file: /admin_stats, /admin_find, /admin_expiring.
"""

import logging
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from db import repo
from handlers.admin.keyboards import (
    PAGE_SIZE,
    admin_list_kb,
    format_list_page,
    format_user_card,
    user_card_kb,
)
from services import channels

_USER_ID_RE = re.compile(r"#id(\d+)")
logger = logging.getLogger(__name__)


def register_admin_commands(dp: Dispatcher) -> None:
    dp.message.register(admin_grant, Command("admin_grant"))
    dp.message.register(admin_revoke, Command("admin_revoke"))
    dp.message.register(admin_list, Command("admin_list"))
    dp.message.register(admin_stats, Command("admin_stats"))
    dp.message.register(admin_find, Command("admin_find"))
    dp.message.register(admin_expiring, Command("admin_expiring"))
    dp.message.register(
        admin_reply_to_user,
        F.from_user.id == settings.ADMIN_ID,
        F.reply_to_message,
        F.text,
        ~F.text.startswith("/"),
    )


def _is_admin(msg: Message) -> bool:
    return msg.from_user.id == settings.ADMIN_ID


# ── existing handlers (migrated verbatim) ─────────────────────────────────────

async def admin_grant(msg: Message, bot: Bot) -> None:
    if not _is_admin(msg):
        return
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.answer("Использование: /admin_grant {tg_id} {product_id}")
        return
    tg_id = int(parts[1])
    product_id = parts[2]
    product = await repo.get_product(product_id, settings.DB_PATH)
    if not product:
        await msg.answer(f"Продукт «{product_id}» не найден.")
        return
    await repo.activate_subscription(tg_id, product_id, order_id="manual", db_path=settings.DB_PATH)
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
    await msg.answer(f"✅ Доступ выдан: tg_id={tg_id} продукт={product_id}")


async def admin_revoke(msg: Message, bot: Bot) -> None:
    if not _is_admin(msg):
        return
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.answer("Использование: /admin_revoke {tg_id} {product_id}")
        return
    tg_id = int(parts[1])
    product_id = parts[2]
    product = await repo.get_product(product_id, settings.DB_PATH)
    if not product:
        await msg.answer(f"Продукт «{product_id}» не найден.")
        return
    await repo.set_subscription_status(tg_id, product_id, "cancelled", settings.DB_PATH)
    await channels.revoke_access(bot, tg_id, product)
    try:
        await bot.send_message(tg_id, "❌ Ваш доступ к каналу был отозван администратором.")
    except Exception as e:
        logger.warning("Не удалось уведомить пользователя %s: %s", tg_id, e)
    await msg.answer(f"✅ Доступ отозван: tg_id={tg_id} продукт={product_id}")


async def admin_list(msg: Message) -> None:
    if not _is_admin(msg):
        return
    subs = await repo.get_active_subscriptions(settings.DB_PATH)
    if not subs:
        await msg.answer("Нет активных подписчиков.")
        return
    total = len(subs)
    page = subs[:PAGE_SIZE]
    text = format_list_page(page, offset=0, total=total)
    kb = admin_list_kb(offset=0, total=total)
    await msg.answer(text, parse_mode="HTML", reply_markup=kb)


async def admin_reply_to_user(msg: Message, bot: Bot) -> None:
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


# ── new command handlers ───────────────────────────────────────────────────────

async def admin_stats(msg: Message) -> None:
    if not _is_admin(msg):
        return
    s = await repo.get_stats(settings.DB_PATH)
    today = datetime.now().strftime("%d.%m.%Y")
    text = (
        f"📊 <b>Статистика на {today}</b>\n"
        "─────────────────────────\n"
        f"👥 Пользователей в боте:    {s['total_users']}\n"
        f"✅ Активных подписок:       {s['active']}\n"
        f"⏳ Ожидают оплаты:          {s['pending']}\n"
        f"❌ Истекших / отменённых:   {s['expired_cancelled']}\n"
        "─────────────────────────\n"
        f"⚠️  Истекают за 7 дней:      {s['expiring_7d']}"
    )
    await msg.answer(text, parse_mode="HTML")


async def admin_find(msg: Message) -> None:
    if not _is_admin(msg):
        return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: /admin_find @username или /admin_find tg_id")
        return
    query = parts[1].strip()
    user = await repo.find_user(settings.DB_PATH, query)
    if not user:
        await msg.answer(f"Пользователь «{query}» не найден.")
        return
    all_products = await repo.get_all_products(settings.DB_PATH)
    text = format_user_card(user)
    kb = user_card_kb(
        tg_id=user["telegram_id"],
        subscriptions=user["subscriptions"],
        all_products=all_products,
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=kb)


async def admin_expiring(msg: Message) -> None:
    if not _is_admin(msg):
        return
    parts = msg.text.split()
    days = 7
    if len(parts) == 2 and parts[1].isdigit():
        days = min(int(parts[1]), 30)
    subs = await repo.get_expiring_subscriptions(settings.DB_PATH, days)
    if not subs:
        await msg.answer(f"Нет истекающих подписок за {days} дней.")
        return
    lines = [f"⏰ <b>Истекают за {days} дней ({len(subs)}):</b>\n"]
    for s in subs:
        until = s["active_until"][:10] if s.get("active_until") else "—"
        user_part = f"@{s['username']}" if s.get("username") else f"ID:{s['telegram_id']}"
        lines.append(f"• {user_part} — {s['product_name']} — до {until}")
    await msg.answer("\n".join(lines), parse_mode="HTML")
