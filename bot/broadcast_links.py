#!/usr/bin/env python3
"""
Рассылает свежие invite-ссылки всем активным подписчикам.

Старые ссылки отзываются перед созданием новых.
Безопасно запускать повторно — идемпотентен.

Запуск:
  docker compose exec bot python broadcast_links.py

  # dry-run (не отправляет сообщения, не меняет БД):
  docker compose exec bot python broadcast_links.py --dry-run
"""

import asyncio
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config import settings

DB_PATH = settings.DB_PATH
DRY_RUN = "--dry-run" in sys.argv


async def revoke_link(bot: Bot, chat_id: int, link: str | None) -> None:
    if not link:
        return
    try:
        await bot.revoke_chat_invite_link(chat_id=chat_id, invite_link=link)
    except Exception as e:
        print(f"    warn: revoke {chat_id} — {e}")


async def main() -> None:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    rows = con.execute("""
        SELECT s.telegram_id, s.product_id,
               s.channel_link, s.discussion_link,
               p.channel_id, p.discussion_id, p.name
        FROM subscriptions s
        JOIN products p USING (product_id)
        WHERE s.status = 'active'
        ORDER BY s.telegram_id
    """).fetchall()

    print(f"Активных подписок: {len(rows)}")
    if DRY_RUN:
        print("DRY-RUN — изменений не будет\n")

    bot = Bot(token=settings.TELEGRAM_TOKEN)
    expire_ts = int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())

    ok = fail = skip = 0

    for row in rows:
        tg_id = row["telegram_id"]
        product_id = row["product_id"]
        product_name = row["name"]
        channel_id = row["channel_id"]
        discussion_id = row["discussion_id"]

        print(f"  tg_id={tg_id} product={product_id}", end=" ")

        if DRY_RUN:
            print("→ пропущен (dry-run)")
            skip += 1
            continue

        try:
            await revoke_link(bot, channel_id, row["channel_link"])
            await revoke_link(bot, discussion_id, row["discussion_link"])

            ch_obj = await bot.create_chat_invite_link(
                chat_id=channel_id, member_limit=1, expire_date=expire_ts
            )
            di_obj = await bot.create_chat_invite_link(
                chat_id=discussion_id, member_limit=1, expire_date=expire_ts
            )
            channel_link = ch_obj.invite_link
            discussion_link = di_obj.invite_link

            now = datetime.now(timezone.utc).isoformat()
            con.execute(
                "UPDATE subscriptions SET channel_link=?, discussion_link=?, updated_at=? "
                "WHERE telegram_id=? AND product_id=?",
                (channel_link, discussion_link, now, tg_id, product_id),
            )
            con.commit()

            await bot.send_message(
                tg_id,
                f"🔗 <b>Ссылки для «{product_name}»</b>\n\n"
                f"Канал: {channel_link}\nБеседа: {discussion_link}\n\n"
                "<i>Ссылки одноразовые и действуют 7 дней.</i>",
                parse_mode="HTML",
            )
            print("→ отправлено")
            ok += 1

        except TelegramForbiddenError:
            print("→ бот заблокирован пользователем, пропущен")
            skip += 1
        except TelegramBadRequest as e:
            print(f"→ ошибка Telegram: {e}")
            fail += 1
        except Exception as e:
            print(f"→ ошибка: {e}")
            fail += 1

        await asyncio.sleep(0.05)  # ~20 msg/s, хватит для любого размера базы

    await bot.session.close()
    con.close()

    print(f"\nИтого: {ok} отправлено, {skip} пропущено, {fail} ошибок")


if __name__ == "__main__":
    asyncio.run(main())
