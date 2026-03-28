"""
Продукты (каналы). Заполни channel_id, discussion_id и prodamus_url
под реальные данные перед запуском. Новый канал — добавить запись и перезапустить.
"""

import aiosqlite

from config import settings

PRODUCTS_TEST = [
    {
        "product_id": "beginner",
        "name": "Начинающий",
        "description": "Базовая программа для новичков. 8 уровней, 28 упражнений.",
        "channel_id": -1003475480396,
        "discussion_id": -1003847085264,
        "prodamus_url": "https://heartpath.payform.ru/",
        "price": 2500,
    },
    {
        "product_id": "intermediate",
        "name": "Промежуточный",
        "description": "Для тех, кто освоил базу. 8 уровней, 28 упражнений.",
        "channel_id": -1003802167188,
        "discussion_id": -5184619005,
        "prodamus_url": "https://heartpath.payform.ru/",
        "price": 2500,
    },
]

PRODUCTS_BASE = [
    {
        "product_id": "base",
        "name": "База",
        "description": "Базовая программа для начинающих. 8 уровней, 28 упражнений.",
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
                (product_id, name, description, channel_id, discussion_id, prodamus_url, price)
            VALUES
                (:product_id, :name, :description, :channel_id, :discussion_id, :prodamus_url, :price)
        """,
            PRODUCTS,
        )
        await db.commit()
