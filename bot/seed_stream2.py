#!/usr/bin/env python3
"""
Seed subscriptions for "2-й поток Калистеника" users.

Запускать ПОСЛЕ того, как пользователи написали боту (иначе их нет в users).

Варианты запуска:
  # внутри контейнера:
  docker compose exec bot python seed_stream2.py

  # на хосте (data/ смонтирован):
  DB_PATH=./data/subscribers.db python seed_stream2.py
"""

import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "/data/subscribers.db")
PRODUCT_ID = "base"

# (username без @, active_until YYYY-MM-DD)
# Год 2026, формат из документа DD.MM.
# 31.06 → 30.06 (в июне 30 дней).
# @MaGGrinK и @KatyaGring — один человек, вставляем оба username.
# Пропущены (нет username): Yuriy Syusko, Сергей Т. Британия,
#   Геннадий Киев, Артур ТАН, Олег Евгеньевич, Денис Лунёв.
STREAM2_USERS: list[tuple[str, str]] = [
    ("meatrich",          "2026-06-30"),  # 31.06 → 30.06 (невалидная дата)
    ("evgely",            "2026-06-18"),
    ("natalya_brykin_a",  "2026-05-31"),
    ("elena250965",       "2026-07-15"),
    ("biya_bravo",        "2026-06-17"),
    ("julaia2608",        "2026-06-17"),
    ("marina_charodeyka", "2026-05-09"),
    ("maggrink",          "2026-06-01"),
    ("katyagring",        "2026-06-01"),  # тот же человек, что @MaGGrinK
    ("skay1202",          "2026-05-30"),
    ("larisa4aykaa",      "2026-04-12"),  # внимание: дата уже завтра
    ("alexantipin",       "2026-05-31"),
    ("d_rossiiskii",      "2026-05-13"),
    ("che_givar",         "2026-05-10"),
    ("andzej88",          "2026-05-27"),  # в документе помечен "?"
]


def main() -> None:
    if not os.path.exists(DB_PATH):
        print(f"ERROR: БД не найдена: {DB_PATH}")
        return

    now = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    seeded = already = not_found = 0

    print(f"БД: {DB_PATH}\nПродукт: {PRODUCT_ID}\n")

    for username, date_str in STREAM2_USERS:
        row = con.execute(
            "SELECT telegram_id FROM users WHERE lower(username) = ?",
            (username,),
        ).fetchone()

        if row is None:
            print(f"  НЕТ В БД    @{username}  (ещё не писал боту)")
            not_found += 1
            continue

        telegram_id = row["telegram_id"]
        active_until = f"{date_str}T23:59:59"

        existing = con.execute(
            "SELECT status, active_until FROM subscriptions "
            "WHERE telegram_id = ? AND product_id = ?",
            (telegram_id, PRODUCT_ID),
        ).fetchone()

        if existing:
            print(
                f"  УЖЕ ЕСТЬ    @{username}  "
                f"status={existing['status']}, until={existing['active_until']}"
            )
            already += 1
            continue

        con.execute(
            """
            INSERT INTO subscriptions
                (telegram_id, product_id, status, active_until, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?, ?)
            """,
            (telegram_id, PRODUCT_ID, active_until, now, now),
        )
        print(f"  ДОБАВЛЕНО   @{username}  telegram_id={telegram_id}  until={active_until}")
        seeded += 1

    con.commit()
    con.close()

    total = seeded + already + not_found
    print(f"\nИтого из {total}: добавлено {seeded}, уже было {already}, не в БД {not_found}")
    if not_found:
        print("Запусти скрипт повторно после того, как оставшиеся напишут боту.")


if __name__ == "__main__":
    main()
