"""
Продукты (каналы). Заполни channel_id, discussion_id и prodamus_url
под реальные данные перед запуском. Новый канал — добавить запись и перезапустить.
"""

import aiosqlite

PRODUCTS = [
    {
        "product_id": "beginner",
        "name": "Начинающий",
        "description": "Базовая программа для новичков. 8 уровней, 28 упражнений.",
        "channel_id": -1001234567890,       # ← заменить
        "discussion_id": -1009876543210,    # ← заменить
        "prodamus_url": "https://demo.payform.ru/",  # ← заменить
        "price": 990,
    },
    {
        "product_id": "intermediate",
        "name": "Промежуточный",
        "description": "Для тех, кто освоил базу. 8 уровней, 28 упражнений.",
        "channel_id": -1001234567891,       # ← заменить
        "discussion_id": -1009876543211,    # ← заменить
        "prodamus_url": "https://demo.payform.ru/",  # ← заменить
        "price": 1290,
    },
]


async def seed_products(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) as cnt FROM products") as cur:
            row = await cur.fetchone()
            if row["cnt"] > 0:
                return  # уже засеяно

        await db.executemany("""
            INSERT OR IGNORE INTO products
                (product_id, name, description, channel_id, discussion_id, prodamus_url, price)
            VALUES
                (:product_id, :name, :description, :channel_id, :discussion_id, :prodamus_url, :price)
        """, PRODUCTS)
        await db.commit()
