"""APScheduler-задачи. Запускаются из main.py lifespan."""

import logging

from aiogram import Bot

from db import repo
from services import channels

logger = logging.getLogger(__name__)


async def check_expired_subscriptions(bot: Bot, db_path: str) -> None:
    """Каждый час проверяет истёкшие активные подписки и кикает пользователей.

    Страховочный механизм — основной триггер кика идёт через Prodamus webhook
    при неудачном рекуррентном платеже.
    """
    expired = await repo.get_expired_active_subscriptions(db_path)
    if not expired:
        return

    logger.info("Found %d expired subscriptions", len(expired))

    for sub in expired:
        tg_id = sub["telegram_id"]
        product_id = sub["product_id"]
        product = {
            "channel_id": sub["channel_id"],
            "discussion_id": sub["discussion_id"],
            "name": sub["product_name"],
        }

        await repo.set_subscription_status(tg_id, product_id, "expired", db_path)
        await channels.revoke_access(bot, tg_id, product)

        try:
            await bot.send_message(
                tg_id,
                f"⏰ <b>Подписка на «{product['name']}» истекла.</b>\n\n"
                "Нажми /start чтобы оформить снова.",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Cannot notify user %s: %s", tg_id, e)

        logger.info("Expired and revoked: tg_id=%s product=%s", tg_id, product_id)
