"""FastAPI-роутер для вебхуков Prodamus."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.context import AppContext
from app import payments
from db import repo
from services.prodamus import verify_signature, _unflatten

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
    ctx: AppContext = request.app.state.app_ctx
    secret: str = request.app.state.prodamus_secret

    form = await request.form()
    post_data: dict[str, str] = {
        k: v for k, v in form.multi_items() if isinstance(v, str)
    }

    incoming_sign = request.headers.get("Sign", "")
    if not verify_signature(post_data, secret, incoming_sign):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(
            "Invalid Prodamus signature from %s, data=%s",
            client_host,
            {k: v for k, v in post_data.items() if k != "Sign"},
        )
        raise HTTPException(status_code=400, detail="Invalid signature")

    nested = _unflatten(post_data)
    payment_status = post_data.get("payment_status", "")
    order_num = post_data.get("order_num", "") or post_data.get("order_id", "")
    amount = post_data.get("sum", "?")

    # Subscription block from Prodamus (present for subscription events)
    sub_block = nested.get("subscription", {})
    action_code = sub_block.get("action_code", "")
    prodamus_sub_id = sub_block.get("id", "")

    # Try to identify user: first from order_num, then from _param_telegram_id,
    # then from prodamus_sub_id mapping in DB (for auto-payments)
    tg_id, product_id = _parse_order_num(order_num)

    if tg_id is None:
        param_tg = post_data.get("_param_telegram_id", "")
        if param_tg.isdigit():
            tg_id = int(param_tg)

    if tg_id is None and prodamus_sub_id:
        existing_sub = await repo.get_subscription_by_prodamus_id(
            prodamus_sub_id, ctx.db_path
        )
        if existing_sub:
            tg_id = existing_sub["telegram_id"]
            product_id = existing_sub["product_id"]

    if product_id is None and sub_block:
        product = await repo.get_product_by_subscription_id(
            int(sub_block.get("subscription_id", 0)), ctx.db_path
        )
        if product:
            product_id = product["product_id"]

    if tg_id is None or product_id is None:
        logger.error(
            "Cannot resolve user/product: order_num=%r sub_block=%r",
            order_num, sub_block,
        )
        return PlainTextResponse("ok")

    logger.info(
        "Prodamus webhook: tg_id=%s product=%s status=%s action=%s order=%s prodamus_sub=%s",
        tg_id, product_id, payment_status, action_code, order_num, prodamus_sub_id,
    )

    await payments.process_payment(
        ctx,
        tg_id=tg_id,
        product_id=product_id,
        order_id=order_num,
        amount=amount,
        payment_status=payment_status,
        action_code=action_code,
        prodamus_sub_id=prodamus_sub_id,
    )
    return PlainTextResponse("ok")


@router.get("/success")
async def payment_success() -> dict:
    return {"message": "Оплата прошла! Вернитесь в Telegram — там уже есть ссылки."}
