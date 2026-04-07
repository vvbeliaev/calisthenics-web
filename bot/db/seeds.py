"""
Продукты (каналы). Заполни channel_id, discussion_id и prodamus_url
под реальные данные перед запуском. Новый канал — добавить запись и перезапустить.
"""

import aiosqlite

from config import settings

PRODUCTS_TEST = [
    {
        "subscription_id": 2834808,
        "product_id": "intermediate",
        "name": "Промежуточный",
        "description": "Для тех, кто освоил базу. 8 уровней, 28 упражнений.",
        "channel_id": -1003802167188,
        "discussion_id": -5184619005,
        "prodamus_url": "https://heartpath.payform.ru/",
        "price": 50,
    },
]

PRODUCTS_BASE = [
    {
        "subscription_id": 2834806,
        "product_id": "base_1_0",
        "name": "BAZA 1.0",
        "description": "Ты только что сделал первый шаг к сильному, гибкому и прокачанному телу — без тренажёров и спортзалов, только с весом своего тела 💪",
        "channel_id": -1003797840314,
        "discussion_id": -1003829594565,
        "prodamus_url": "https://heartpath.payform.ru/",
        "price": 2500,
    },
]

PRODUCTS = PRODUCTS_TEST if settings.TEST_MODE else PRODUCTS_BASE


async def seed_products(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) as cnt FROM products") as cur:
            row = await cur.fetchone()
            if row and row["cnt"] > 0:
                return  # уже засеяно

        await db.executemany(
            """
            INSERT OR IGNORE INTO products
                (product_id, name, description, channel_id, discussion_id, prodamus_url, price, subscription_id)
            VALUES
                (:product_id, :name, :description, :channel_id, :discussion_id, :prodamus_url, :price, :subscription_id)
        """,
            PRODUCTS,
        )
        await db.commit()
