from aiogram import types
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.slide_controllers import get_slide_picture, get_slide_text
from core.database.models import Lesson, UserProgress
from core.keyboards.futher_button import get_further_button


async def get_lesson_slide_amount(lesson_number: int, session: AsyncSession) -> Lesson.slide_amount:
    query = select(Lesson).filter(Lesson.id == lesson_number)
    result: Result = await session.execute(query)
    lesson = result.scalar()
    return lesson.slide_amount


async def lesson_routine(callback: types.CallbackQuery, lesson_number: int, current_slide: int, slide_amount: int, session: AsyncSession) -> None:
    # TODO: assert
    if current_slide < slide_amount:
        text = await get_slide_text(lesson_number=lesson_number, slide_number=current_slide, session=session)
        image_file = await get_slide_picture(lesson_number=lesson_number, slide_number=current_slide, session=session)
        path = f'core/resources/images/lesson{lesson_number}/{image_file}'
        
        # TODO: not always has text and photo

        await callback.message.answer(text=text)
        await callback.message.answer_photo(photo=types.FSInputFile(path=path),
                                            reply_markup=get_further_button(current_slide=current_slide))

