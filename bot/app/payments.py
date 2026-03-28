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
    success: bool,
) -> None:
    """Handle a Prodamus payment callback (success or failure)."""
    from ui import keyboards, messages

    if not success:
        sub = await repo.get_subscription(tg_id, product_id, ctx.db_path)
        if sub and sub["status"] == "active":
            product = await repo.get_product(product_id, ctx.db_path)
            if product:
                await repo.set_subscription_status(tg_id, product_id, "cancelled", ctx.db_path)
                await channels.revoke_access(ctx.bot, tg_id, product)
            try:
                await ctx.bot.send_message(
                    tg_id,
                    messages.format_payment_failed(),
                    parse_mode="HTML",
                )
            except Exception:
                pass
        return

    product = await repo.get_product(product_id, ctx.db_path)
    if not product:
        logger.error("Product not found: %s", product_id)
        return

    try:
        channel_link, discussion_link = await subscriptions.grant(
            ctx, tg_id, product_id, order_id, notify_user=False
        )
        await ctx.bot.send_message(
            tg_id,
            messages.format_payment_success(product["name"], channel_link, discussion_link),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("grant / notify user failed: %s", e)
        return

    try:
        await _notify_admin(ctx, tg_id, product, amount, order_id)
    except Exception as e:
        logger.error("notify_admin failed: %s", e)


async def _notify_admin(
    ctx: AppContext,
    tg_id: int,
    product: dict,
    amount: str,
    order_id: str,
) -> None:
    from ui import keyboards, messages

    username_info = ""
    try:
        chat = await ctx.bot.get_chat(tg_id)
        username_info = f"@{chat.username} " if chat.username else ""
    except Exception:
        pass

    await ctx.bot.send_message(
        settings.ADMIN_ID,
        messages.format_payment_notification(
            username_info, tg_id, product["name"], amount, order_id
        ),
        parse_mode="HTML",
        reply_markup=keyboards.payment_notification_kb(tg_id, product["product_id"]),
    )
