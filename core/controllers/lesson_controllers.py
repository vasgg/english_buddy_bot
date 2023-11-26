import asyncio

from aiogram import types
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.slide_controllers import get_slide
from core.database.models import Lesson
from core.keyboards.keyboard_builders import get_furher_button
from core.resources.enums import KeyboardType, SlideType


async def get_lesson_slide_amount(lesson_number: int, session: AsyncSession) -> Lesson.slide_amount:
    query = select(Lesson).filter(Lesson.id == lesson_number)
    result: Result = await session.execute(query)
    lesson = result.scalar()
    return lesson.slide_amount


async def lesson_routine(callback: types.CallbackQuery, lesson_number: int, current_slide: int, slide_amount: int, session: AsyncSession) -> None:
    assert current_slide < slide_amount
    slide = await get_slide(lesson_number=lesson_number, slide_number=current_slide, session=session)
    match slide.slide_type:
        case SlideType.TEXT:
            text = slide.text
            if not slide.keyboard_type:
                await callback.message.answer(text=text)
                if slide.delay:
                    await asyncio.sleep(int(slide.delay))
                await lesson_routine(callback=callback, lesson_number=lesson_number, current_slide=current_slide + 1,
                                     slide_amount=slide_amount, session=session)
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_number, current_slide=current_slide)
                        await callback.message.answer(text=text,
                                                      reply_markup=markup)
                    case KeyboardType.QUIZ:
                        ...
        case SlideType.IMAGE:
            image_file = slide.picture
            path = f'core/resources/images/lesson{lesson_number}/{image_file}'
            if not slide.keyboard_type:
                await callback.message.answer_photo(photo=types.FSInputFile(path=path))
                if slide.delay:
                    await asyncio.sleep(int(slide.delay))
                await lesson_routine(callback=callback, lesson_number=lesson_number, current_slide=current_slide + 1,
                                     slide_amount=slide_amount, session=session)
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_number, current_slide=current_slide)
                        await callback.message.answer_photo(photo=types.FSInputFile(path=path),
                                                            reply_markup=markup)
                    case KeyboardType.QUIZ:
                        ...
        case SlideType.STICKER:
            ...
        case SlideType.QUIZ_OPTIONS:
            ...
        case SlideType.QUIZ_INPUT_WORD:
            ...
        case SlideType.QUIZ_INPUT_PHRASE:
            ...
        case _:
            assert False, f'Unknown slide type: {slide.slide_type}'

