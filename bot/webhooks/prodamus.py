"""FastAPI-роутер для вебхуков Prodamus."""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.context import AppContext
from app import payments
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
    ctx: AppContext = request.app.state.app_ctx
    secret: str = request.app.state.prodamus_secret

    form = await request.form()
    post_data: dict[str, str] = {k: v for k, v in form.multi_items() if isinstance(v, str)}

    incoming_sign = request.headers.get("Sign", "")
    if not verify_signature(post_data, secret, incoming_sign):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(
            "Invalid Prodamus signature from %s, data=%s",
            client_host,
            {k: v for k, v in post_data.items() if k != "Sign"},
        )
        raise HTTPException(status_code=400, detail="Invalid signature")

    payment_status = post_data.get("payment_status", "")
    order_num = post_data.get("order_num", "") or post_data.get("order_id", "")
    amount = post_data.get("sum", "?")

    tg_id, product_id = _parse_order_num(order_num)
    if tg_id is None or product_id is None:
        logger.error("Cannot parse tg_id/product_id from order_num=%r", order_num)
        return PlainTextResponse("ok")

    logger.info(
        "Prodamus webhook: tg_id=%s product=%s status=%s order=%s",
        tg_id, product_id, payment_status, order_num,
    )

    await payments.process_payment(
        ctx, tg_id, product_id, order_num, amount, success=(payment_status == "success")
    )
    return PlainTextResponse("ok")


@router.get("/success")
async def payment_success() -> dict:
    return {"message": "Оплата прошла! Вернитесь в Telegram — там уже есть ссылки."}
