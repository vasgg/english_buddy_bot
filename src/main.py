import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.controllers.user_controllers import check_user_reminders
from bot.database.db import db
from bot.handlers.command_handlers import router as base_router
from bot.handlers.errors_handler import router as errors_router
from bot.handlers.lesson_handlers import router as lesson_router
from bot.handlers.session_handlers import router as quiz_router
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.middlewares.session_middlewares import DBSessionMiddleware
from bot.middlewares.updates_dumper_middleware import UpdatesDumperMiddleware
from bot.resources.commands import set_bot_commands
from bot.resources.notify_admin import on_shutdown_notify, on_startup_notify


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s: " "%(filename)s: " "%(levelname)s: " "%(funcName)s(): " "%(lineno)d:\t" "%(message)s",
    )

    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode="HTML")
    # TODO: change to persistent storage
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)
    dispatcher.message.middleware(DBSessionMiddleware())
    dispatcher.callback_query.middleware(DBSessionMiddleware())
    dispatcher.message.middleware(AuthMiddleware())
    dispatcher.callback_query.middleware(AuthMiddleware())
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(set_bot_commands)
    dispatcher.startup.register(on_startup_notify)
    dispatcher.shutdown.register(on_shutdown_notify)
    dispatcher.include_routers(base_router, errors_router, lesson_router, quiz_router)
    task = asyncio.create_task(check_user_reminders(bot=bot, db_connector=db))
    await dispatcher.start_polling(bot)


def run_main():
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
