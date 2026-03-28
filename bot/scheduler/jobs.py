"""APScheduler-задачи. Запускаются из main.py lifespan."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from app.context import AppContext
from app import subscriptions

logger = logging.getLogger(__name__)


async def check_expired_subscriptions(ctx: AppContext) -> None:
    await subscriptions.check_and_expire(ctx)


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

    with sqlite3.connect(src) as src_conn, sqlite3.connect(dest) as dst_conn:
        src_conn.backup(dst_conn)

    logger.info("Database backup created: %s", dest)

    backups = sorted(dest_dir.glob(f"{src.stem}_*.db"))
    for old in backups[:-keep]:
        old.unlink()
        logger.info("Old backup removed: %s", old)
