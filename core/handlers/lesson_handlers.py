from aiogram import F, Router, types
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import get_lesson_slide_amount, lesson_routine
from core.controllers.user_controllers import check_user_progress
from core.database.models import User

router = Router()


@router.callback_query(F.data.startswith('lesson_'))
async def lesson_callback_processing(callback: types.CallbackQuery, user: User, session: AsyncSession) -> None:
    lesson_number = int(callback.data.split('_')[1])
    progress = await check_user_progress(user_id=user.id, lesson_number=lesson_number, session=session)
    slide_amount = await get_lesson_slide_amount(lesson_number=lesson_number, session=session)
    await callback.message.answer(text=f'lesson: {lesson_number} total slides: {slide_amount}, current slide: {progress}')
    await lesson_routine(callback=callback, lesson_number=lesson_number, current_slide=progress, slide_amount=slide_amount, session=session)
    await callback.answer()


@router.callback_query(F.data.startswith('next_slide_'))
async def next_slide_callback_processing(callback: types.CallbackQuery, user: User, session: AsyncSession) -> None:
    slide_number = int(callback.data.split('_')[2])
    # progress = await check_user_progress(user_id=user.id, lesson_number=lesson_number, session=session)
    # if progress < c
    # slide_amount = await get_lesson_slide_amount(lesson_number=lesson_number, session=session)
    # await callback.message.answer(text=f'lesson: {lesson_number} total slides: {slide_amount}, current slide: {progress}')
    # await lesson_routine(callback=callback, lesson_number=lesson_number, current_slide=progress, slide_amount=slide_amount, session=session)
    # await callback.answer()
