import asyncio
import logging.config
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
import sentry_sdk

from bot.controllers.user_controllers import check_user_reminders, daily_routine
from bot.handlers.command_handlers import router as base_router
from bot.handlers.errors_handler import router as errors_router
from bot.handlers.lesson_handlers import router as lesson_router
from bot.handlers.premium_handlers import router as premium_router
from bot.handlers.session_handlers import router as quiz_router
from bot.internal.commands import set_bot_commands
from bot.internal.notify_admin import on_shutdown_notify, on_startup_notify
from bot.middlewares.auth_middleware import AuthMiddleware
from bot.middlewares.session_middlewares import DBSessionMiddleware
from bot.middlewares.updates_dumper_middleware import UpdatesDumperMiddleware
from config import get_logging_config, get_settings
from database.tables_helper import get_db
from enums import Stage


async def main():
    logs_directory = Path("logs")
    logs_directory.mkdir(parents=True, exist_ok=True)
    logging_config = get_logging_config(__name__)
    logging.config.dictConfig(logging_config)
    settings = get_settings()

    if settings.SENTRY_AIOGRAM_DSN and settings.STAGE == Stage.PROD:
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
    redis = Redis(db=1)
    storage = RedisStorage(redis)
    db = get_db()
    dispatcher = Dispatcher(storage=storage)
    db_session_middleware = DBSessionMiddleware(db)
    dispatcher.message.middleware(db_session_middleware)
    dispatcher.callback_query.middleware(db_session_middleware)
    dispatcher.message.middleware(AuthMiddleware())
    dispatcher.callback_query.middleware(AuthMiddleware())
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(set_bot_commands)
    dispatcher.startup.register(on_startup_notify)
    dispatcher.shutdown.register(on_shutdown_notify)
    dispatcher.include_routers(base_router, errors_router, lesson_router, quiz_router, premium_router)
    # noinspection PyUnusedLocal
    reminders_task = asyncio.create_task(check_user_reminders(bot=bot, db_connector=db))
    # noinspection PyUnusedLocal
    daily_task = asyncio.create_task(daily_routine(bot=bot, db_connector=db))
    await dispatcher.start_polling(bot)


def run_main():
    asyncio.run(main())


if __name__ == '__main__':
    run_main()
