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
        "channel_id": -1003475480396,       # ← заменить
        "discussion_id": -1003847085264,    # ← заменить
        "prodamus_url": "https://demo.payform.ru/",  # ← заменить
        "price": 2500,
    },
    {
        "product_id": "intermediate",
        "name": "Промежуточный",
        "description": "Для тех, кто освоил базу. 8 уровней, 28 упражнений.",
        "channel_id": -1003802167188,       # ← заменить
        "discussion_id": -5184619005,    # ← заменить
        "prodamus_url": "https://demo.payform.ru/",  # ← заменить
        "price": 2500,
    },
    {
        "product_id": "demo",
        "name": "Демо",
        "description": "Для тех, кто освоил базу. 8 уровней, 28 упражнений.",
        "channel_id": -1003802167188,       # ← заменить
        "discussion_id": -5184619005,    # ← заменить
        "prodamus_url": "https://demo.payform.ru/",  # ← заменить
        "price": 2500,
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
