"""Subscription use cases: grant, revoke, relink, expire."""

import logging
from datetime import datetime

from app.context import AppContext
from db import repo
from services import channels

logger = logging.getLogger(__name__)


async def grant(
    ctx: AppContext,
    tg_id: int,
    product_id: str,
    order_id: str,
    days: int = 30,
    notify_user: bool = True,
) -> tuple[str, str]:
    """Activate subscription + grant channel access.

    Returns (channel_link, discussion_link).
    If notify_user=True, sends standard access-granted DM to the user.
    """
    product = await repo.get_product(product_id, ctx.db_path)
    if not product:
        raise ValueError(f"Продукт «{product_id}» не найден.")
    await repo.activate_subscription(
        tg_id, product_id,
        order_id=order_id,
        db_path=ctx.db_path,
        days=days,
    )
    channel_link, discussion_link = await channels.grant_access(ctx.bot, tg_id, product)
    if notify_user:
        from ui import messages

        try:
            await ctx.bot.send_message(
                tg_id,
                messages.format_access_granted(
                    product["name"], channel_link, discussion_link
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Cannot notify user %s: %s", tg_id, e)
    return channel_link, discussion_link


async def revoke(
    ctx: AppContext,
    tg_id: int,
    product_id: str,
    notify_user: bool = True,
) -> None:
    """Cancel subscription + revoke channel access.

    If notify_user=True, sends access-revoked DM to the user.
    """
    product = await repo.get_product(product_id, ctx.db_path)
    if not product:
        raise ValueError(f"Продукт «{product_id}» не найден.")
    await repo.set_subscription_status(tg_id, product_id, "cancelled", ctx.db_path)
    await channels.revoke_access(ctx.bot, tg_id, product)
    if notify_user:
        from ui import messages

        try:
            await ctx.bot.send_message(tg_id, messages.format_access_revoked())
        except Exception as e:
            logger.warning("Cannot notify user %s: %s", tg_id, e)


async def relink(ctx: AppContext, tg_id: int, product_id: str) -> tuple[str, str]:
    """Create fresh invite links for an active subscriber.

    Returns (channel_link, discussion_link).
    Raises ValueError if subscription is not active.
    """
    product = await repo.get_product(product_id, ctx.db_path)
    sub = await repo.get_subscription(tg_id, product_id, ctx.db_path)
    if not product or not sub or sub["status"] != "active":
        raise ValueError("Подписка неактивна.")
    return await channels.grant_access(ctx.bot, tg_id, product)


async def grant_test(ctx: AppContext, tg_id: int, product_id: str) -> tuple[str, str]:
    """TEST_MODE: grant with active_until=now so the scheduler picks it up quickly.

    Returns (channel_link, discussion_link).
    """
    product = await repo.get_product(product_id, ctx.db_path)
    if not product:
        raise ValueError(f"Продукт «{product_id}» не найден.")
    await repo.upsert_subscription(
        telegram_id=tg_id,
        product_id=product_id,
        status="active",
        active_until=datetime.utcnow().isoformat(),
        db_path=ctx.db_path,
    )
    logger.info("TEST_MODE: granted %s to %s (expires now)", product_id, tg_id)
    return await channels.grant_access(ctx.bot, tg_id, product)


async def get_user_subs(ctx: AppContext, tg_id: int) -> list[dict]:
    return await repo.get_subscriptions(tg_id, ctx.db_path)


async def check_and_expire(ctx: AppContext) -> None:
    """Scheduler task: find overdue active subscriptions, expire + revoke + notify."""
    from ui import messages

    expired = await repo.get_expired_active_subscriptions(ctx.db_path)
    if not expired:
        return

    logger.info("Found %d expired subscriptions", len(expired))
    for sub in expired:
        tg_id = sub["telegram_id"]
        product_id = sub["product_id"]
        product = {
            "channel_id": sub["channel_id"],
            "discussion_id": sub["discussion_id"],
            "name": sub["product_name"],
        }
        await repo.set_subscription_status(tg_id, product_id, "expired", ctx.db_path)
        await channels.revoke_access(ctx.bot, tg_id, product)
        try:
            await ctx.bot.send_message(
                tg_id,
                messages.format_subscription_expired(sub["product_name"]),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Cannot notify user %s: %s", tg_id, e)
        logger.info("Expired and revoked: tg_id=%s product=%s", tg_id, product_id)
