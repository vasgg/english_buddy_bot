import asyncio
from pathlib import Path

from aiogram import types

from bot.keyboards.keyboards import get_further_button
from database.models.session import Session
from database.models.slide import Slide
from enums import KeyboardType


async def process_image(
    event: types.Message,
    slide: Slide,
    session: Session,
) -> bool:
    markup = None
    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    image_path = Path(f"src/webapp/static/lessons_images/{session.lesson_id}/{slide.picture}")
    if not image_path.exists():
        image_path = Path("src/webapp/static/lessons_images/Image_not_available.png")
    if slide.keyboard_type == KeyboardType.FURTHER:
        markup = get_further_button()
    await event.answer_photo(photo=types.FSInputFile(path=image_path), reply_markup=markup)
    return slide.keyboard_type != KeyboardType.FURTHER
