import asyncio
import logging.config

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import sentry_sdk

from bot.controllers.user_controllers import check_user_reminders
from bot.handlers.command_handlers import router as base_router
from bot.handlers.errors_handler import router as errors_router
from bot.handlers.lesson_handlers import router as lesson_router
from bot.handlers.session_handlers import router as quiz_router
from bot.internal.commands import set_bot_commands
from bot.internal.notify_admin import on_shutdown_notify, on_startup_notify
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.middlewares.session_middlewares import DBSessionMiddleware
from bot.middlewares.updates_dumper_middleware import UpdatesDumperMiddleware
from config import get_logging_config, settings
from database.db import db


async def main():
    logging_config = get_logging_config(__name__)
    logging.config.dictConfig(logging_config)

    sentry_sdk.init(
        dsn=settings.SENTRY_AIOGRAM_DSN.get_secret_value(),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode='HTML')
    logging.info("bot started")

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


if __name__ == '__main__':
    run_main()
