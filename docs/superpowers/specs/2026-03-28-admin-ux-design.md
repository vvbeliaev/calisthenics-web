# Admin UX Improvements — Design Spec

**Date:** 2026-03-28
**Status:** Approved
**Scope:** Telegram bot admin panel, ~250 subscribers

---

## Problem

Current admin capabilities don't scale to 250 subscribers:
- `/admin_list` dumps all records in one unpaginated message (Telegram truncates at ~4096 chars)
- `grant`/`revoke` require knowing `tg_id` by heart — no user lookup
- Payment notifications are passive text — no one-click actions
- No visibility into subscription health (stats, expiring soon)

---

## Solution Overview

Add 5 admin features split across a clean `handlers/admin/` subpackage:

1. **Inline buttons on payment notification** — one-click grant/revoke
2. **`/admin_find`** — search user by @username or tg_id, show card with action buttons
3. **`/admin_stats`** — single-message dashboard
4. **`/admin_expiring [days]`** — list subscriptions expiring within N days
5. **Paginated `/admin_list`** — 20 records per page via stateless callback_data

---

## File Structure

### New: `bot/handlers/admin/` subpackage

```
bot/handlers/admin/
  __init__.py      re-exports register_admin_handlers (thin)
  commands.py      command handlers: /admin_stats, /admin_find, /admin_list, /admin_expiring
                   also: admin_grant, admin_revoke, admin_reply_to_user (moved from old admin.py)
  callbacks.py     all inline keyboard callback handlers
                   also: notify_admin (moved from old admin.py, now with keyboard)
  keyboards.py     InlineKeyboardMarkup builders (pure functions, no I/O)
```

### Deleted
- `bot/handlers/admin.py` — replaced by the subpackage above

### Unchanged
- `bot/handlers/client.py`
- `bot/services/` — no changes
- `bot/webhooks/prodamus.py` — import path for `notify_admin` updates
- `bot/scheduler/jobs.py` — no changes
- `bot/main.py` — only `set_my_commands` gains 3 new entries

### Extended: `bot/db/repo.py`

Three new async functions:

```python
async def get_stats(db_path: str) -> dict
# Returns: {total_users, active, pending, expired_cancelled, expiring_7d}

async def get_expiring_subscriptions(db_path: str, days: int) -> list[dict]
# Subscriptions where status='active' AND active_until < now + days
# Joined with users table: username, first_name

async def find_user(db_path: str, query: str) -> dict | None
# Searches users by username (strip @) or telegram_id (if query is numeric)
# Returns: {"telegram_id", "username", "first_name", "first_seen", "last_seen",
#           "subscriptions": [{"product_id", "name", "status", "active_until"}, ...]}
# Returns None if not found
```

---

## Feature Designs

### 1. Inline buttons on payment notification

`notify_admin` updated to attach an inline keyboard:

```
💰 Новая оплата!
Пользователь: @username (12345)
Продукт: Базовый курс — 2990 ₽
Order ID: abc123

[✅ Выдать доступ]  [❌ Отозвать]
```

Callback data format:
- `apay_grant:{tg_id}:{product_id}`
- `apay_revoke:{tg_id}:{product_id}`

On `apay_grant` callback: perform the action, then **edit** the original notification message — replace keyboard with a status line (e.g., `✅ Выдан @username 28.03.2026 12:34`). This prevents duplicate actions.

On `apay_revoke` callback: since revoking a just-paid subscription is unusual, the button triggers a two-step confirm — edit message to show `[Точно отозвать?] [Отмена]` before executing. Callback data for confirm: `apay_revoke_confirm:{tg_id}:{product_id}`.

Access is still granted **automatically** by the webhook on successful payment. These buttons are for manual edge cases (offline payment, discount, override).

---

### 2. `/admin_find <query>`

Query can be `@username`, `username` (without @), or a numeric `tg_id`.

Response — user card with per-product action buttons:

```
👤 @username (ID: 12345)
Имя: Алексей
Первый визит: 01.01.2026 · Последний: 27.03.2026

Подписки:
• Базовый курс — active до 15.04.2026
• Продвинутый — не оформлен

[❌ Отозвать: Базовый]  [✅ Выдать: Продвинутый]
```

Callback data: `afind_revoke:{tg_id}:{product_id}` / `afind_grant:{tg_id}:{product_id}`

On callback: perform action, edit message to confirm, re-render updated card.

If user not found: plain reply "Пользователь не найден".

---

### 3. `/admin_stats`

No inline keyboard. Single message, always current data.

```
📊 Статистика на 28.03.2026
─────────────────────────
👥 Пользователей в боте:   247
✅ Активных подписок:      189
⏳ Ожидают оплаты:          31
❌ Истекших / отменённых:   27
─────────────────────────
⚠️  Истекают за 7 дней:     14
```

---

### 4. `/admin_expiring [days]`

Default: 7 days. Max accepted: 30.

Plain text list (typically few records, no pagination needed):

```
⏰ Истекают за 7 дней (3):

• @alice (12345) — Базовый курс — до 01.04.2026
• @bob (67890) — Продвинутый — до 02.04.2026
• (нет username) ID:11111 — Базовый курс — до 03.04.2026
```

If empty: "Нет истекающих подписок за X дней."

---

### 5. Paginated `/admin_list`

Page size: 20. Stateless — offset encoded in callback_data.

Initial `/admin_list` shows page 0. Navigation buttons appear only when relevant:

```
Активные подписки (189):

• @alice — Базовый курс — до 01.04.2026
• @bob — Продвинутый — до 15.04.2026
... (20 rows)

[→ Далее (20–39)]          ← no "back" on first page
```

Callback data: `alist:{offset}`

On callback: edit the message in place (no new messages, no spam).

---

## `main.py` changes

Add 3 commands to admin scope in `set_my_commands`:

```python
BotCommand(command="admin_stats",    description="Статистика подписок"),
BotCommand(command="admin_find",     description="Найти пользователя: /admin_find @username"),
BotCommand(command="admin_expiring", description="Истекают скоро: /admin_expiring [days]"),
```

---

## Constraints & Non-Goals

- No FSM — pagination is fully stateless via callback_data
- No broadcast (`/admin_broadcast`) — out of scope for this iteration
- No CSV export — out of scope
- No user notes — out of scope
- `handlers/client.py` untouched
- `scheduler/jobs.py` untouched
- SQLite stays — no schema changes needed (all new queries use existing tables)
