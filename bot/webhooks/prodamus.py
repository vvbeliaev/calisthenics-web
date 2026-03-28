"""FastAPI-роутер для вебхуков Prodamus."""

import logging

from aiogram import Bot
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from db import repo
from handlers.admin.callbacks import notify_admin
from services import channels
from services.prodamus import verify_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment")


def _parse_order_num(order_num: str) -> tuple[int, str] | tuple[None, None]:
    """Извлекает tg_id и product_id из order_num вида tg_{tg_id}_{product_id}_{ts}."""
    parts = order_num.split("_", 3)
    if len(parts) >= 3 and parts[0] == "tg":
        try:
            return int(parts[1]), parts[2]
        except ValueError:
            pass
    return None, None


@router.post("/webhook")
async def payment_webhook(request: Request) -> PlainTextResponse:
    """Prodamus шлёт POST после каждого платежа (успешного и нет).

    tg_id и product_id вытаскиваются из order_num (формат: tg_{tg_id}_{product_id}_{ts}).
    Это позволяет использовать статический URL вебхука в настройках Prodamus.
    """
    bot: Bot = request.app.state.bot
    db_path: str = request.app.state.db_path
    secret: str = request.app.state.prodamus_secret

    form = await request.form()
    post_data = dict(form)

    incoming_sign = request.headers.get("Sign", "")
    if not verify_signature(post_data, secret, incoming_sign):
        logger.warning(
            "Invalid Prodamus signature from %s, data=%s",
            request.client.host,
            {k: v for k, v in post_data.items() if k != "Sign"},
        )
        raise HTTPException(status_code=400, detail="Invalid signature")

    payment_status = post_data.get("payment_status", "")
    order_num = post_data.get("order_num", "") or post_data.get("order_id", "")
    amount = post_data.get("sum", "?")

    tg_id, product_id = _parse_order_num(order_num)
    if tg_id is None:
        logger.error("Cannot parse tg_id/product_id from order_num=%r", order_num)
        return PlainTextResponse("ok")

    logger.info(
        "Prodamus webhook: tg_id=%s product=%s status=%s order=%s",
        tg_id, product_id, payment_status, order_num,
    )

    # Неудачный платёж — кикаем и уведомляем
    if payment_status != "success":
        sub = await repo.get_subscription(tg_id, product_id, db_path)
        if sub and sub["status"] == "active":
            product = await repo.get_product(product_id, db_path)
            if product:
                await repo.set_subscription_status(tg_id, product_id, "cancelled", db_path)
                await channels.revoke_access(bot, tg_id, product)
            try:
                await bot.send_message(
                    tg_id,
                    "❌ <b>Оплата не прошла.</b>\n\n"
                    "Подписка отменена. Нажми /start чтобы оформить снова.",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        return PlainTextResponse("ok")

    # Успешная оплата
    product = await repo.get_product(product_id, db_path)
    if not product:
        logger.error("Product not found: %s", product_id)
        return PlainTextResponse("ok")

    await repo.activate_subscription(tg_id, product_id, order_num, db_path)

    try:
        channel_link, discussion_link = await channels.grant_access(bot, tg_id, product)
        await bot.send_message(
            tg_id,
            f"🎉 <b>Оплата прошла!</b>\n\n"
            f"Добро пожаловать в «{product['name']}»!\n\n"
            f"Канал: {channel_link}\n"
            f"Беседа: {discussion_link}\n\n"
            "<i>Ссылки одноразовые, действуют 7 дней.\n"
            "Если понадобятся снова — нажми /start.</i>",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("grant_access / notify user failed: %s", e)

    try:
        await notify_admin(bot, tg_id, product, amount, order_num)
    except Exception as e:
        logger.error("notify_admin failed: %s", e)

    return PlainTextResponse("ok")


@router.get("/success")
async def payment_success() -> dict:
    return {"message": "Оплата прошла! Вернитесь в Telegram — там уже есть ссылки."}
