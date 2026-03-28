# Telegram Bot — Design Spec

**Date:** 2026-03-27
**Project:** Caliathletics
**Status:** Approved

---

## Overview

Telegram-бот для монетизации приватных каналов. Один бот обслуживает три контура: клиентский онбординг/покупка, управление доступом к каналам, панель менеджера.

---

## Контуры системы

### 1. Клиентский контур

Пользователь открывает бота → видит каталог продуктов (inline-кнопки) → получает ссылку на оплату Prodamus → оплачивает (Prodamus собирает контакты сам) → получает одноразовую ссылку-приглашение в канал + беседу.

### 2. Контур доступа к каналам

Бот является администратором в каждом приватном канале и прикреплённой беседе. После успешной оплаты генерирует одноразовую invite-ссылку (`createChatInviteLink`, `member_limit=1`). При истечении подписки или неудачном рекуррентном платеже — кикает пользователя (`banChatMember` + немедленный `unbanChatMember` чтобы разрешить вернуться в будущем).

### 3. Менеджерский контур

Пользователь с `ADMIN_ID` получает уведомления о каждой новой оплате. Может вручную выдавать и отзывать доступ через команды `/admin_grant` и `/admin_revoke`.

---

## Технический стек

| Компонент              | Выбор                                          |
| ---------------------- | ---------------------------------------------- |
| Telegram-клиент        | aiogram 3                                      |
| HTTP-сервер (webhooks) | FastAPI                                        |
| База данных            | SQLite через aiosqlite                         |
| Планировщик задач      | APScheduler (AsyncIOScheduler)                 |
| Запуск                 | uvicorn, бот в polling-режиме через `lifespan` |
| Python                 | 3.13+                                          |
| Пакетный менеджер      | uv (через pyproject.toml)                      |

> SQLite выбран как простое и надёжное решение для текущего масштаба. Легко мигрировать на Postgres при необходимости (достаточно поменять aiosqlite на asyncpg в `db/repo.py`).

---

## Структура файлов

```
bot/
├── main.py                  # точка входа, lifespan, uvicorn
├── config.py                # настройки из .env (pydantic-settings)
├── handlers/
│   ├── __init__.py
│   ├── client.py            # /start, каталог, кнопка оплаты
│   └── admin.py             # /admin_grant, /admin_revoke, /admin_list
├── services/
│   ├── __init__.py
│   ├── subscriptions.py     # бизнес-логика подписок
│   └── channels.py          # invite links, kick/unban
├── db/
│   ├── __init__.py
│   ├── init.py              # CREATE TABLE IF NOT EXISTS (products, users, subscriptions)
│   ├── seeds.py             # начальные данные о продуктах
│   └── repo.py              # CRUD: products, users, subscriptions
├── webhooks/
│   ├── __init__.py
│   └── prodamus.py          # POST /payment/webhook, GET /payment/success
├── scheduler/
│   ├── __init__.py
│   └── jobs.py              # check_expired_subscriptions (каждый час)
├── pyproject.toml
└── .env.example
```

---

## База данных

### Таблица `products`

```sql
CREATE TABLE IF NOT EXISTS products (
    product_id    TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    description   TEXT,
    channel_id    INTEGER NOT NULL,   -- Telegram channel ID
    discussion_id INTEGER NOT NULL,   -- linked discussion group ID
    prodamus_url  TEXT NOT NULL,      -- базовый URL формы Prodamus
    price         INTEGER NOT NULL    -- цена в рублях
);
```

Продукты определяются в `db/seeds.py` как список Python-словарей и вставляются функцией `seed_products()` при запуске (только если таблица пуста). Для добавления нового канала — добавить запись в `seeds.py` и перезапустить.

### Таблица `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    telegram_id   INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    first_seen    TEXT NOT NULL,   -- ISO datetime UTC
    last_seen     TEXT NOT NULL
);
```

Upsert при каждом `/start`. Даёт общий счётчик лидов для воронки.

### Таблица `subscriptions`

```sql
CREATE TABLE IF NOT EXISTS subscriptions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id   INTEGER NOT NULL,
    product_id    TEXT NOT NULL REFERENCES products(product_id),
    active_until  TEXT,            -- NULL пока status='pending'
    order_id      TEXT,            -- из Prodamus
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending | active | expired | cancelled
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    UNIQUE(telegram_id, product_id)
);
```

**Жизненный цикл статуса:**

- `pending` — создаётся когда пользователь нажимает "Купить" (клик по inline-кнопке продукта)
- `active` — переходит при успешном webhook от Prodamus, `active_until` заполняется
- `expired` — APScheduler переводит когда `active_until < now()`
- `cancelled` — Prodamus прислал webhook с неудачным платежом

**Воронка из одного запроса:**

```sql
SELECT
    (SELECT COUNT(*) FROM users)                                        AS total_leads,
    COUNT(CASE WHEN status = 'pending'   THEN 1 END)                   AS in_checkout,
    COUNT(CASE WHEN status = 'active'    THEN 1 END)                   AS paying,
    COUNT(CASE WHEN status = 'expired'   THEN 1 END)                   AS churned,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END)                   AS payment_failed
FROM subscriptions;
```

---

## Флоу клиента (детально)

```
/start
  └─→ handlers/client.py::cmd_start()
        └─→ db/repo.py::upsert_user(tg_id, username, first_name)   # фиксируем лид
        └─→ db/repo.py::get_subscriptions(tg_id)                   # все статусы
        └─→ Показать каталог: название, цена, статус (активна / в оформлении / не куплена)
              [кнопка "Купить" для новых]
              [кнопка "Получить ссылку снова" для active]
              [кнопка "Оформить снова" для expired/cancelled]

callback "buy:{product_id}"
  └─→ handlers/client.py::cb_buy()
        └─→ db/repo.py::get_product(product_id)
        └─→ db/repo.py::upsert_subscription(tg_id, product_id, status="pending")  # фиксируем интерес
        └─→ services/subscriptions.py::build_payment_url(tg_id, product)
              order_id = f"tg_{tg_id}_{product_id}_{timestamp}"
              url_notification = f"{WEBHOOK_BASE_URL}/payment/webhook?tg_id={tg_id}&product_id={product_id}"
        └─→ Отправить кнопку с URL платёжной формы
```

---

## Флоу оплаты и выдачи доступа

```
POST /payment/webhook?tg_id=X&product_id=Y
  └─→ webhooks/prodamus.py::payment_webhook()
        └─→ Проверка подписи Prodamus
        └─→ Если payment_status != "success" → 200 OK (ничего не делаем)
        └─→ db/repo.py::upsert_subscription(tg_id, product_id, +30 дней)
        └─→ services/channels.py::grant_access(bot, tg_id, product)
              createChatInviteLink(channel_id, member_limit=1, expire_date=+7 дней)
              createChatInviteLink(discussion_id, member_limit=1, expire_date=+7 дней)
        └─→ Отправить пользователю сообщение с двумя ссылками
        └─→ Уведомить ADMIN_ID: кто оплатил, какой продукт, сумма
        └─→ 200 OK ("ok")
```

> Invite-ссылки действуют 7 дней — пользователь должен успеть перейти. Если не успел — нажимает `/start`, каталог покажет кнопку "Получить ссылку снова" для активных подписок.

---

## Авторекуррент и отзыв доступа

**Успешный рекуррентный платёж** → тот же `POST /payment/webhook` со статусом `success` → продление `active_until += 30 дней`.

**Неудачный платёж** → Prodamus шлёт webhook со статусом `fail` →

```
webhooks/prodamus.py
  └─→ db/repo.py::set_subscription_status(tg_id, product_id, "cancelled")
  └─→ services/channels.py::revoke_access(bot, tg_id, product)
        banChatMember(channel_id, tg_id)
        unbanChatMember(channel_id, tg_id)   # сразу, чтобы мог вернуться
        banChatMember(discussion_id, tg_id)
        unbanChatMember(discussion_id, tg_id)
  └─→ Уведомить пользователя: "Подписка отменена, оплата не прошла"
```

**APScheduler (каждый час)** — страховочный механизм:

```
scheduler/jobs.py::check_expired_subscriptions()
  └─→ db/repo.py::get_expired_active_subscriptions()
        SELECT * FROM subscriptions
        WHERE status = 'active' AND active_until < datetime('now')
  └─→ Для каждой: revoke_access() + set_subscription_status("expired")
```

---

## Менеджерский контур

Все команды доступны только при `message.from_user.id == ADMIN_ID`.

| Команда                              | Действие                                             |
| ------------------------------------ | ---------------------------------------------------- |
| `/admin_grant {tg_id} {product_id}`  | Выдать доступ вручную (active_until = now + 30 дней) |
| `/admin_revoke {tg_id} {product_id}` | Отозвать доступ вручную                              |
| `/admin_list`                        | Список активных подписок (текстом)                   |

Уведомление при каждой оплате:

```
💰 Новая оплата!
Пользователь: @username (tg_id)
Продукт: Название канала
Сумма: 990 ₽
Order ID: tg_123_product1_...
```

---

## Конфигурация (.env)

```env
TELEGRAM_TOKEN=
ADMIN_ID=                        # Telegram ID менеджера
WEBHOOK_BASE_URL=https://...     # публичный URL сервера
PRODAMUS_SECRET=                 # ключ для проверки подписи
DB_PATH=subscribers.db
```

Продукты при первом запуске вставляются через `db/init.py` из переменных окружения или захардкоженного seed-файла.

---

## Деплой (MVP)

- Один процесс: `uvicorn bot.main:app --host 0.0.0.0 --port 8000`
- Бот работает в polling-режиме (запускается в `lifespan`)
- Для продакшна: systemd unit или docker-контейнер
- SQLite-файл монтируется как volume при docker-деплое
- Webhook URL Prodamus настраивается вручную в личном кабинете Prodamus

---

## Что за рамками MVP (на потом)

- Broadcast-рассылка по подписчикам
- Статистика (активные, выручка)
- Web-admin панель
- Миграция на Postgres
- Webhook-mode вместо polling для бота
