import typing

import aiogram
from aiogram import Router

from bot.internal.notify_admin import notify_admin_about_exception

if typing.TYPE_CHECKING:
    from aiogram.types.error_event import ErrorEvent

router = Router()


@router.errors()
async def error_handler(error_event: "ErrorEvent", bot: aiogram.Bot):
    exc_info = error_event.exception
    context = f"dispatcher error ({type(error_event.update).__name__})" if error_event.update else "dispatcher error"
    await notify_admin_about_exception(bot, exc_info, context=context)
