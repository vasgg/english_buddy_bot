from contextlib import suppress

from aiogram import types
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound


async def process_dict(
    event: types.Message,
    text: str,
) -> bool:
    msg = await event.answer(text=text)
    with suppress(TelegramBadRequest, TelegramForbiddenError, TelegramNotFound):
        await msg.pin(disable_notification=True)
    return True
