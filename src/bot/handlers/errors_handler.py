import logging
import typing

import aiogram

from bot.config import settings

if typing.TYPE_CHECKING:
    from aiogram.types.error_event import ErrorEvent

from aiogram import Router

router = Router()


@router.errors()
async def error_handler(_: "ErrorEvent", bot: aiogram.Bot):
    logging.exception("Exception:")
    # TODO: send exception log to telegram admin
    await bot.send_message(settings.ADMINS[0], "Something went wrong")
