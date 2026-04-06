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
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    Update,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Response

from app.admin_ui import router as admin_ui_router
from app.context import AppContext
from config import settings
from db.init import init_tables
from db.seeds import seed_products
from handlers.admin import register_admin_handlers
from handlers.client import register_client_handlers
from scheduler.jobs import backup_database, check_expired_subscriptions
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

    # AppContext — единый объект зависимостей для всего приложения
    ctx = AppContext(bot=bot, db_path=settings.DB_PATH)
    dp["app"] = ctx          # aiogram DI: handlers receive it as `app: AppContext`
    app.state.app_ctx = ctx  # FastAPI state: webhooks access it via request.app.state.app_ctx
    app.state.prodamus_secret = settings.PRODAMUS_SECRET

    # Хендлеры
    register_client_handlers(dp)
    register_admin_handlers(dp)

    # Меню команд
    await bot.set_my_commands(
        [BotCommand(command="start", description="Каталог программ и оформление подписки")],
        scope=BotCommandScopeDefault(),
    )
    await bot.set_my_commands(
        [
            BotCommand(command="start",          description="Каталог программ и оформление подписки"),
            BotCommand(command="admin_stats",    description="Статистика подписок"),
            BotCommand(command="admin_find",     description="Найти пользователя: /admin_find @username"),
            BotCommand(command="admin_list",     description="Список активных подписчиков"),
            BotCommand(command="admin_expiring", description="Истекают скоро: /admin_expiring [days=3]"),
            BotCommand(command="admin_grant",    description="Выдать доступ: /admin_grant tg_id product_id"),
            BotCommand(command="admin_revoke",   description="Отозвать доступ: /admin_revoke tg_id product_id"),
        ],
        scope=BotCommandScopeChat(chat_id=settings.ADMIN_ID),
    )

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_expired_subscriptions,
        trigger="interval",
        minutes=5,
        args=[ctx],
        id="check_expired",
        misfire_grace_time=60,
    )
    scheduler.add_job(
        backup_database,
        trigger="interval",
        hours=4,
        args=[settings.DB_PATH],
        id="backup_db",
    )
    scheduler.start()

    polling_task = None

    if settings.WEBHOOK_BASE_URL:
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/bot/webhook"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("Webhook set: %s", webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, starting polling...")
        polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))

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
app.include_router(admin_ui_router)


@app.post("/bot/webhook")
async def bot_webhook(request: Request) -> Response:
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot=bot, update=update)
    return Response()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
