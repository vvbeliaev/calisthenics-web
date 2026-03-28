"""Admin query use cases: stats, user lookup, subscription lists."""

from app.context import AppContext
from db import repo


async def get_stats(ctx: AppContext) -> dict:
    return await repo.get_stats(ctx.db_path)


async def find_user(ctx: AppContext, query: str) -> dict | None:
    return await repo.find_user(ctx.db_path, query)


async def list_subscriptions(ctx: AppContext) -> list[dict]:
    return await repo.get_active_subscriptions(ctx.db_path)


async def list_expiring(ctx: AppContext, days: int = 3) -> list[dict]:
    return await repo.get_expiring_subscriptions(ctx.db_path, days)


async def get_products(ctx: AppContext) -> list[dict]:
    return await repo.get_all_products(ctx.db_path)


async def get_product(ctx: AppContext, product_id: str) -> dict | None:
    return await repo.get_product(product_id, ctx.db_path)


async def upsert_user(
    ctx: AppContext,
    tg_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    await repo.upsert_user(tg_id, username, first_name, ctx.db_path)
