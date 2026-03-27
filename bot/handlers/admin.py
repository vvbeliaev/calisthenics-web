"""Менеджерский контур: уведомления и ручное управление доступом."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from db import repo
from services import channels

logger = logging.getLogger(__name__)


def register_admin_handlers(dp: Dispatcher) -> None:
    dp.message.register(admin_grant, Command("admin_grant"))
    dp.message.register(admin_revoke, Command("admin_revoke"))
    dp.message.register(admin_list, Command("admin_list"))


def _is_admin(msg: Message) -> bool:
    return msg.from_user.id == settings.ADMIN_ID


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
            f"Канал: {channel_link}\n"
            f"Беседа: {discussion_link}\n\n"
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

    subs = await _get_active_subs()
    if not subs:
        await msg.answer("Нет активных подписчиков.")
        return

    lines = [f"<b>Активные подписки ({len(subs)}):</b>\n"]
    for s in subs:
        until = s["active_until"][:10] if s["active_until"] else "—"
        lines.append(f"• tg={s['telegram_id']} | {s['product_id']} | до {until}")

    await msg.answer("\n".join(lines), parse_mode="HTML")


async def _get_active_subs() -> list[dict]:
    async with __import__("aiosqlite").connect(settings.DB_PATH) as db:
        db.row_factory = __import__("aiosqlite").Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE status = 'active' ORDER BY active_until"
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def notify_admin(bot: Bot, tg_id: int, product: dict, amount: str, order_id: str) -> None:
    """Вызывается из webhook после успешной оплаты."""
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
    )
