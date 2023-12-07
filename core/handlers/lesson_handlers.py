from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import get_lesson, lesson_routine
from core.controllers.session_controller import update_session_status, get_current_session
from core.controllers.user_controllers import update_session
from core.database.models import Session, User
from core.keyboards.callback_builders import LessonStartsFromCallbackFactory, LessonsCallbackFactory
from core.keyboards.keyboards import get_lesson_progress_keyboard
from core.resources.enums import LessonStartsFrom, SessionStatus, SessonStartsFrom, UserLessonProgress

router = Router()


async def common_processing(bot: Bot, user: User, lesson_id: int, slide_id: int, session: Session,
                            state: FSMContext, db_session: AsyncSession, starts_from: SessonStartsFrom) -> None:
    await update_session(user_id=user.id, lesson_id=lesson_id, current_slide_id=slide_id,
                         session_id=session.id, starts_from=starts_from, db_session=db_session)
    await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id, state=state,
                         starts_from=starts_from, db_session=db_session, session_id=session.id)


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(callback: types.CallbackQuery, callback_data: LessonsCallbackFactory, user: User,
                                     state: FSMContext, db_session: AsyncSession) -> None:
    data = await state.get_data()
    await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=data['start_msg_id'])
    session: Session = await get_current_session(user_id=user.id, lesson_id=callback_data.lesson_id, db_session=db_session)
    if not session:
        msg = await callback.message.answer(text='Вы можете начать урок сначала, или сразу перейти к экзамену.',
                                            reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.NO_PROGRESS,
                                                                                            lesson_id=callback_data.lesson_id, session=db_session))
    else:
        msg = await callback.message.answer(text='Вы можете продолжить урок, или начать его сначала.',
                                            reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.IN_PROGRESS,
                                                                                            lesson_id=callback_data.lesson_id,
                                                                                            current_slide=session.current_slide_id,
                                                                                            session=db_session))
    await state.update_data(start_from_msg_id=msg.message_id)
    await callback.answer()


@router.callback_query(LessonStartsFromCallbackFactory.filter())
async def lesson_start_from_callback_processing(callback: types.CallbackQuery, callback_data: LessonStartsFromCallbackFactory,
                                                bot: Bot, user: User, state: FSMContext, db_session: AsyncSession) -> None:
    data = await state.get_data()
    await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=data['start_from_msg_id'])

    lesson_id = callback_data.lesson_id
    slide_id = callback_data.slide_id
    attr = callback_data.attr
    lesson = await get_lesson(lesson_id=lesson_id, db_session=db_session)

    match attr:
        case LessonStartsFrom.BEGIN:
            session = await get_current_session(user_id=user.id, lesson_id=lesson_id, db_session=db_session)
            if session:
                await update_session_status(session_id=session.id, status=SessionStatus.IN_PROGRESS, new_status=SessionStatus.ABORTED,
                                            db_session=db_session)
            session = Session(user_id=user.id, lesson_id=lesson_id, current_slide_id=slide_id, starts_from=SessonStartsFrom.BEGIN)
            db_session.add(session)
            await db_session.flush()
            await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=lesson.first_slide_id,
                                    state=state, starts_from=SessonStartsFrom.BEGIN, session=session, db_session=db_session)
        case LessonStartsFrom.EXAM:
            session = await get_current_session(user_id=user.id, lesson_id=lesson_id, db_session=db_session)
            if session:
                await update_session_status(session_id=session.id, status=SessionStatus.IN_PROGRESS, new_status=SessionStatus.ABORTED,
                                            db_session=db_session)
            session = Session(user_id=user.id, lesson_id=lesson_id, current_slide_id=lesson.exam_slide_id, starts_from=SessonStartsFrom.EXAM)
            db_session.add(session)
            await db_session.flush()
            await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=lesson.exam_slide_id,
                                    state=state, session=session, starts_from=SessonStartsFrom.EXAM, db_session=db_session)
        case LessonStartsFrom.CONTINUE:
            session = await get_current_session(user_id=user.id, lesson_id=lesson_id, db_session=db_session)
            await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=session.current_slide_id,
                                    state=state, session=session, starts_from=session.starts_from, db_session=db_session)
        case _:
            assert False, 'invalid attr'
    await state.update_data(session_id=session.id)
    await callback.answer()
