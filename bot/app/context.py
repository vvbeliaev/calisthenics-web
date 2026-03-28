from dataclasses import dataclass

from aiogram import Bot


@dataclass
class AppContext:
    bot: Bot
    db_path: str
