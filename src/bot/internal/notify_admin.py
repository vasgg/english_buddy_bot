import logging
import traceback
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound

from config import get_settings


async def on_startup_notify(bot: Bot):
    bot_info = await bot.get_me()
    try:
        await bot.send_message(
            get_settings().ADMIN,
            f'{bot_info.username} started\n\n/start',
            disable_notification=True,
        )
    except (TelegramForbiddenError, TelegramNotFound) as exc:
        logging.warning("Unable to notify admin about startup: %s", exc)


async def on_shutdown_notify(bot: Bot):
    bot_info = await bot.get_me()
    try:
        await bot.send_message(
            get_settings().ADMIN,
            f'{bot_info.username} shutdown',
            disable_notification=True,
        )
    except (TelegramForbiddenError, TelegramNotFound) as exc:
        logging.warning("Unable to notify admin about shutdown: %s", exc)


def build_exception_message(exc: BaseException, *, context: Optional[str] = None) -> str:
    exc_traceback = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    tb_tail = exc_traceback[-3500:]
    header = "🚨 <b>An error occurred</b> 🚨"
    if context:
        header = f"{header}\n<b>Context:</b> {context}"
    return (
        f"{header}\n\n"
        f"<b>Type:</b> {type(exc).__name__}\n"
        f"<b>Message:</b> {exc}\n\n"
        f"<b>Traceback:</b>\n<code>{tb_tail}</code>"
    )


async def notify_admin_about_exception(bot: Bot, exc: BaseException, *, context: Optional[str] = None) -> None:
    logging.exception("Exception in %s", context or "background task", exc_info=exc)
    try:
        await bot.send_message(get_settings().ADMIN, build_exception_message(exc, context=context))
    except (TelegramForbiddenError, TelegramNotFound) as notify_exc:
        logging.warning("Unable to notify admin about exception in %s: %s", context or "background task", notify_exc)
