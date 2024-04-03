import asyncio

from aiogram import types
from bot.keyboards.keyboards import get_further_button
from database.models.slide import Slide
from enums import KeyboardType


async def process_text(
    event: types.Message,
    slide: Slide,
) -> bool:
    markup = None
    if slide.keyboard_type == KeyboardType.FURTHER:
        markup = get_further_button()
    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    await event.answer(
        text=slide.text,
        reply_markup=markup,
    )
    return slide.keyboard_type != KeyboardType.FURTHER
