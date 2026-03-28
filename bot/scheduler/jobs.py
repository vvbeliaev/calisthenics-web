"""APScheduler-задачи. Запускаются из main.py lifespan."""

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

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


def backup_database(db_path: str, backup_dir: str = "backups", keep: int = 10) -> None:
    """Создаёт резервную копию SQLite-базы и удаляет старые, оставляя `keep` последних."""
    src = Path(db_path)
    if not src.exists():
        logger.warning("backup_database: source %s not found, skipping", src)
        return

    dest_dir = Path(backup_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{src.stem}_{timestamp}.db"

    # sqlite3.connect.backup — безопасное копирование даже при активных транзакциях
    with sqlite3.connect(src) as src_conn, sqlite3.connect(dest) as dst_conn:
        src_conn.backup(dst_conn)

    logger.info("Database backup created: %s", dest)

    # Удаляем лишние файлы, оставляем `keep` самых свежих
    backups = sorted(dest_dir.glob(f"{src.stem}_*.db"))
    for old in backups[:-keep]:
        old.unlink()
        logger.info("Old backup removed: %s", old)
