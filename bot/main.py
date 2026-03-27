"""Точка входа. Запуск: uvicorn main:app --host 0.0.0.0 --port 8000"""

import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from config import settings
from db.init import init_tables
from db.seeds import seed_products
from handlers.client import register_client_handlers
from handlers.admin import register_admin_handlers
from scheduler.jobs import check_expired_subscriptions
from webhooks.prodamus import router as payment_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # БД
    await init_tables(settings.DB_PATH)
    await seed_products(settings.DB_PATH)

    # Бот
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    dp = Dispatcher()
    register_client_handlers(dp)
    register_admin_handlers(dp)

    # Расшариваем bot и настройки для вебхуков
    app.state.bot = bot
    app.state.db_path = settings.DB_PATH
    app.state.prodamus_secret = settings.PRODAMUS_SECRET

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_expired_subscriptions,
        trigger="interval",
        hours=1,
        args=[bot, settings.DB_PATH],
        id="check_expired",
    )
    scheduler.start()

    # Polling в фоне
    polling_task = asyncio.create_task(
        dp.start_polling(bot, handle_signals=False)
    )

    logger.info("Bot started (polling mode)")
    yield

    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    scheduler.shutdown(wait=False)
    await bot.session.close()
    logger.info("Bot stopped")


app = FastAPI(title="Caliathletics Bot", lifespan=lifespan)
app.include_router(payment_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
