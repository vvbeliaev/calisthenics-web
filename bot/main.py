"""Точка входа.

Webhook-режим (продакшн):
    Задай WEBHOOK_BASE_URL в .env.
    Telegram будет слать апдейты на POST /bot/webhook.
    Запуск: uvicorn main:app --host 0.0.0.0 --port 8000

Polling-режим (локальная разработка):
    Оставь WEBHOOK_BASE_URL пустым — бот сам удалит webhook и запустит polling.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Response

from config import settings
from db.init import init_tables
from db.seeds import seed_products
from handlers.admin import register_admin_handlers
from handlers.client import register_client_handlers
from scheduler.jobs import check_expired_subscriptions
from webhooks.prodamus import router as payment_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.TELEGRAM_TOKEN)
dp = Dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # БД
    await init_tables(settings.DB_PATH)
    await seed_products(settings.DB_PATH)

    # Хендлеры
    register_client_handlers(dp)
    register_admin_handlers(dp)

    # Расшариваем для вебхуков оплаты
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

    polling_task = None

    if settings.WEBHOOK_BASE_URL:
        # ── Webhook-режим ──────────────────────────────────────────────────
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/bot/webhook"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("Webhook set: %s", webhook_url)
    else:
        # ── Polling-режим ──────────────────────────────────────────────────
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, starting polling...")
        polling_task = asyncio.create_task(
            dp.start_polling(bot, handle_signals=False)
        )

    yield

    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    if settings.WEBHOOK_BASE_URL:
        await bot.delete_webhook()

    scheduler.shutdown(wait=False)
    await bot.session.close()
    logger.info("Bot stopped")


app = FastAPI(title="Caliathletics Bot", lifespan=lifespan)
app.include_router(payment_router)


@app.post("/bot/webhook")
async def bot_webhook(request: Request) -> Response:
    """Принимает апдейты от Telegram в webhook-режиме."""
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot=bot, update=update)
    return Response()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
