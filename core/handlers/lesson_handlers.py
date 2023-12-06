from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import lesson_routine
from core.controllers.user_controllers import get_lesson_progress, update_session
from core.database.models import User
from core.keyboards.callback_builders import LessonStartFromCallbackFactory, LessonsCallbackFactory, SlideCallbackFactory
from core.keyboards.keyboards import get_lesson_progress_keyboard
from core.resources.enums import StartsFrom, UserLessonProgress

router = Router()


async def common_processing(bot: Bot, user: User, lesson_id: int, slide_id: int,
                            state: FSMContext, session: AsyncSession, starts_from: StartsFrom = StartsFrom.BEGIN) -> None:
    await update_session(user_id=user.id, lesson_id=lesson_id, current_slide_id=slide_id, starts_from=starts_from, session=session)
    await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id, state=state, session=session)


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(callback: types.CallbackQuery, callback_data: LessonsCallbackFactory, user: User,
                                     state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=data['start_msg_id'])
    progress = await get_lesson_progress(user_id=user.id, lesson_id=callback_data.lesson_id, session=session)
    # TODO:
    # Передавать через callback_data признак того, начали ли с начала|экзмена или продолжили
    # чтобы в lesson_start_from_callback_processing можно было определить, нужно ли
    # начинать новую сессию
    if not progress:
        msg = await callback.message.answer(text='Вы можете начать урок сначала, или сразу перейти к экзамену.',
                                            reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.NO_PROGRESS,
                                                                                            lesson_id=callback_data.lesson_id, session=session))
    else:
        msg = await callback.message.answer(text='Вы можете продолжить урок, или начать его сначала.',
                                            reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.IN_PROGRESS,
                                                                                            lesson_id=callback_data.lesson_id,
                                                                                            current_slide=progress,
                                                                                            session=session))
    await state.update_data(start_from_msg_id=msg.message_id)
    await callback.answer()


@router.callback_query(LessonStartFromCallbackFactory.filter())
async def lesson_start_from_callback_processing(callback: types.CallbackQuery, callback_data: LessonStartFromCallbackFactory,
                                                bot: Bot, user: User, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=data['start_from_msg_id'])

    # TODO: создать новую сессию, если начали сначала или с экзамена

    lesson_id = callback_data.lesson_id
    slide_id = callback_data.slide_id
    if not slide_id:
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=1, state=state, session=session)
    else:
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id, state=state, session=session)
    await callback.answer()


# кинуть в квиз и сюда тоже передавать сессию
@router.callback_query(SlideCallbackFactory.filter())
async def slide_callback_processing(callback: types.CallbackQuery, bot: Bot, callback_data: SlideCallbackFactory, user: User,
                                    state: FSMContext, session: AsyncSession) -> None:
    lesson_id = callback_data.lesson_id
    next_slide_id = callback_data.next_slide_id
    await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=next_slide_id, state=state, session=session)
    await callback.answer()


