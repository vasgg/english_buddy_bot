from aiogram import F, Router, types
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import get_lesson_slide_amount, lesson_routine
from core.controllers.user_controllers import get_user_progress
from core.database.models import User
from core.keyboards.callback_builders import LessonsCallbackFactory, SlideCallbackFactory

router = Router()


async def common_callback_processing(callback: types.CallbackQuery, user: User, lesson_number: int, slide_number: int, session: AsyncSession) -> None:
    progress = await get_user_progress(user_id=user.id, lesson_number=lesson_number, slide_number=slide_number, session=session)
    slide_amount = await get_lesson_slide_amount(lesson_number=lesson_number, session=session)
    await lesson_routine(callback=callback, lesson_number=lesson_number, current_slide=progress, slide_amount=slide_amount, session=session)
    await callback.answer()


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(callback: types.CallbackQuery,
                                     callback_data: LessonsCallbackFactory,
                                     user: User,
                                     session: AsyncSession) -> None:
    await common_callback_processing(callback=callback, user=user, lesson_number=callback_data.lesson_number, slide_number=1, session=session)


@router.callback_query(SlideCallbackFactory.filter())
async def slide_callback_processing(callback: types.CallbackQuery,
                                    callback_data: SlideCallbackFactory,
                                    user: User,
                                    session: AsyncSession) -> None:
    lesson_number = callback_data.lesson_number
    slide_number = callback_data.slide_number
    await common_callback_processing(callback=callback, user=user, lesson_number=lesson_number, slide_number=slide_number, session=session)


