"""Управление доступом к приватным Telegram-каналам и беседам."""

import logging
from datetime import datetime, timedelta

from aiogram import Bot

logger = logging.getLogger(__name__)


async def grant_access(bot: Bot, telegram_id: int, product: dict) -> tuple[str, str]:
    """Создаёт одноразовые invite-ссылки для канала и беседы (7 дней).

    Бот должен быть администратором в обоих чатах.
    Возвращает (channel_link, discussion_link).
    """
    expire_ts = int((datetime.utcnow() + timedelta(days=7)).timestamp())

    channel_obj = await bot.create_chat_invite_link(
        chat_id=product["channel_id"],
        member_limit=1,
        expire_date=expire_ts,
    )
    discussion_obj = await bot.create_chat_invite_link(
        chat_id=product["discussion_id"],
        member_limit=1,
        expire_date=expire_ts,
    )
    return channel_obj.invite_link, discussion_obj.invite_link


async def revoke_access(bot: Bot, telegram_id: int, product: dict) -> None:
    """Кикает пользователя из канала и беседы.

    После ban сразу unban — чтобы пользователь мог вернуться по новой ссылке.
    """
    for chat_id in (product["channel_id"], product["discussion_id"]):
        try:
            await bot.ban_chat_member(chat_id=chat_id, user_id=telegram_id)
            await bot.unban_chat_member(chat_id=chat_id, user_id=telegram_id)
        except Exception as e:
            logger.warning("revoke_access chat=%s user=%s: %s", chat_id, telegram_id, e)
