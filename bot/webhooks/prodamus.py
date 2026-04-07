"""FastAPI-роутер для вебхуков Prodamus."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.context import AppContext
from app import payments
from services.prodamus import verify_signature, _unflatten

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment")


def _parse_order_num(order_num: str) -> tuple[int, str] | tuple[None, None]:
    """Извлекает tg_id и product_id из order_num вида tg_{tg_id}_{product_id}_{ts}.

    product_id может содержать подчёркивания, поэтому timestamp отрезаем справа.
    """
    parts = order_num.split("_")
    if len(parts) >= 4 and parts[0] == "tg":
        try:
            tg_id = int(parts[1])
            product_id = "_".join(parts[2:-1])
            return tg_id, product_id
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
    if sub_block:
        logger.info("Prodamus subscription block: %s", sub_block)
    logger.info(
        "Prodamus identifiers: order_num=%r _param_telegram_id=%r",
        order_num, post_data.get("_param_telegram_id"),
    )
    action_code = sub_block.get("action_code", "")

    # Identify user: from order_num, then from _param_telegram_id
    tg_id, product_id = _parse_order_num(order_num)

    if tg_id is None:
        param_tg = post_data.get("_param_telegram_id", "")
        if param_tg.isdigit():
            tg_id = int(param_tg)

    if tg_id is None or product_id is None:
        logger.error(
            "Cannot resolve user/product: order_num=%r _param_telegram_id=%r",
            order_num, post_data.get("_param_telegram_id"),
        )
        return PlainTextResponse("ok")

    logger.info(
        "Prodamus webhook: tg_id=%s product=%s status=%s action=%s order=%s",
        tg_id, product_id, payment_status, action_code, order_num,
    )

    await payments.process_payment(
        ctx,
        tg_id=tg_id,
        product_id=product_id,
        order_id=order_num,
        amount=amount,
        payment_status=payment_status,
        action_code=action_code,
    )
    return PlainTextResponse("ok")


@router.get("/success")
async def payment_success() -> dict:
    return {"message": "Оплата прошла! Вернитесь в Telegram — там уже есть ссылки."}
