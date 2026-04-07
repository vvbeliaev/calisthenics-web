"""Payment processing use case."""

import logging

from app.context import AppContext
from app import subscriptions
from config import settings
from db import repo
from services import channels

logger = logging.getLogger(__name__)


async def process_payment(
    ctx: AppContext,
    tg_id: int,
    product_id: str,
    order_id: str,
    amount: str,
    payment_status: str,
    action_code: str = "",
    prodamus_sub_id: str = "",
) -> None:
    """Handle a Prodamus payment/subscription callback.

    action_code values for subscriptions:
      - "" (empty)       — initial payment (first subscription charge)
      - "auto_payment"   — recurring auto-charge succeeded
      - "deactivation"   — subscription deactivated
      - "finish"         — subscription finished (all charges done)

    payment_status: "success" or other (failure).
    """
    from ui import keyboards, messages

    success = payment_status == "success"

    if action_code in ("deactivation", "finish"):
        await _handle_deactivation(ctx, tg_id, product_id, action_code)
        return

    if not success:
        await _handle_failure(ctx, tg_id, product_id)
        return

    # Success: initial payment or auto_payment — activate/extend subscription
    product = await repo.get_product(product_id, ctx.db_path)
    if not product:
        logger.error("Product not found: %s", product_id)
        return

    is_auto = action_code == "auto_payment"

    try:
        channel_link, discussion_link = await subscriptions.grant(
            ctx, tg_id, product_id, order_id,
            prodamus_sub_id=prodamus_sub_id,
            notify_user=False,
        )
        if is_auto:
            await ctx.bot.send_message(
                tg_id,
                messages.format_subscription_renewed(product["name"]),
                parse_mode="HTML",
            )
        else:
            await ctx.bot.send_message(
                tg_id,
                messages.format_payment_success(
                    product["name"], channel_link, discussion_link
                ),
                parse_mode="HTML",
            )
    except Exception as e:
        logger.error("grant / notify user failed: %s", e)
        return

    try:
        await _notify_admin(ctx, tg_id, product, amount, order_id, is_auto)
    except Exception as e:
        logger.error("notify_admin failed: %s", e)


async def _handle_deactivation(
    ctx: AppContext,
    tg_id: int,
    product_id: str,
    action_code: str,
) -> None:
    """Handle subscription deactivation or finish."""
    from ui import messages

    product = await repo.get_product(product_id, ctx.db_path)
    if not product:
        return

    await repo.set_subscription_status(tg_id, product_id, "cancelled", ctx.db_path)
    await channels.revoke_access(ctx.bot, tg_id, product)

    try:
        await ctx.bot.send_message(
            tg_id,
            messages.format_subscription_deactivated(product["name"]),
            parse_mode="HTML",
        )
    except Exception:
        pass

    logger.info(
        "Subscription %s for tg_id=%s product=%s",
        action_code, tg_id, product_id,
    )


async def _handle_failure(
    ctx: AppContext,
    tg_id: int,
    product_id: str,
) -> None:
    """Handle failed payment (initial or auto-charge)."""
    from ui import messages

    sub = await repo.get_subscription(tg_id, product_id, ctx.db_path)
    if sub and sub["status"] == "active":
        product = await repo.get_product(product_id, ctx.db_path)
        if product:
            await repo.set_subscription_status(
                tg_id, product_id, "cancelled", ctx.db_path
            )
            await channels.revoke_access(ctx.bot, tg_id, product)
    try:
        await ctx.bot.send_message(
            tg_id,
            messages.format_payment_failed(),
            parse_mode="HTML",
        )
    except Exception:
        pass


async def _notify_admin(
    ctx: AppContext,
    tg_id: int,
    product: dict,
    amount: str,
    order_id: str,
    is_auto: bool = False,
) -> None:
    from ui import keyboards, messages

    username_info = ""
    try:
        chat = await ctx.bot.get_chat(tg_id)
        username_info = f"@{chat.username} " if chat.username else ""
    except Exception:
        pass

    label = "Auto-payment" if is_auto else "Payment"
    await ctx.bot.send_message(
        settings.ADMIN_ID,
        messages.format_payment_notification(
            username_info, tg_id, product["name"], amount, order_id, label=label
        ),
        parse_mode="HTML",
        reply_markup=keyboards.payment_notification_kb(tg_id, product["product_id"]),
    )
