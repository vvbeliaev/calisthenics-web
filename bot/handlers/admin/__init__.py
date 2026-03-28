"""Admin handlers subpackage.

External contract: `from handlers.admin import register_admin_handlers`
This is the only import other modules should use.
"""

from aiogram import Dispatcher

from handlers.admin.callbacks import register_admin_callbacks
from handlers.admin.commands import register_admin_commands


def register_admin_handlers(dp: Dispatcher) -> None:
    register_admin_commands(dp)
    register_admin_callbacks(dp)
