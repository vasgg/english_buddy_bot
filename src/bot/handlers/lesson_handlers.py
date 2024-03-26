from aiogram import Bot, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.lesson_controllers import find_first_exam_slide_id
from bot.controllers.session_controller import session_routine
from bot.controllers.user_controllers import show_start_menu
from bot.keyboards.callback_data import (
    LessonStartsFromCallbackFactory,
    LessonsCallbackFactory,
    RemindersCallbackFactory,
)
from bot.keyboards.keyboards import get_lesson_progress_keyboard
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import get_lesson_by_id
from database.crud.session import get_current_session, update_session_status
from database.crud.user import set_user_reminders
from database.models.session import Session
from database.models.user import User
from enums import LessonStartsFrom, SessionStatus, UserLessonProgress, lesson_to_session

router = Router()


async def lesson_routine(
    bot: Bot,
    user: User,
    slide_id: int,
    session: Session,
    state: FSMContext,
    db_session: AsyncSession,
    skip_step_increment: bool = False,
) -> None:
    step = session.current_step + 1 if not skip_step_increment else session.current_step
    await session_routine(bot, user, slide_id, step, state, session, db_session)


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(
    callback: types.CallbackQuery,
    callback_data: LessonsCallbackFactory,
    user: User,
    db_session: AsyncSession,
) -> None:
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    session = await get_current_session(user_id=user.id, lesson_id=callback_data.lesson_id, db_session=db_session)
    lesson = await get_lesson_by_id(lesson_id=callback_data.lesson_id, db_session=db_session)
    slides_count = len(lesson.path.split('.'))
    if slides_count == 0:
        await callback.message.answer(text='no slides yet')
        return
    path: list[int] = [int(elem) for elem in lesson.path.split(".")]
    first_exam_slide = await find_first_exam_slide_id(path, db_session)
    if lesson.is_paid and user.paywall_access is False:
        await callback.message.answer(text=await get_text_by_prompt(prompt='paywall_message', db_session=db_session))
        return
    if session:
        await callback.message.answer(
            text=await get_text_by_prompt(prompt='starts_from_with_progress', db_session=db_session),
            reply_markup=await get_lesson_progress_keyboard(
                mode=UserLessonProgress.IN_PROGRESS,
                lesson=lesson,
                exam_slide_id=first_exam_slide,
                current_slide_id=session.current_slide_id,
            ),
        )
    else:
        if first_exam_slide:
            await callback.message.answer(
                text=await get_text_by_prompt(prompt='starts_from_with_exam', db_session=db_session),
                reply_markup=await get_lesson_progress_keyboard(
                    mode=UserLessonProgress.NO_PROGRESS, lesson=lesson, exam_slide_id=first_exam_slide
                ),
            )
        else:
            await callback.message.answer(
                text=await get_text_by_prompt(prompt='starts_from_without_exam', db_session=db_session),
                reply_markup=await get_lesson_progress_keyboard(
                    mode=UserLessonProgress.NO_PROGRESS, lesson=lesson, exam_slide_id=first_exam_slide
                ),
            )
    await callback.answer()


@router.callback_query(LessonStartsFromCallbackFactory.filter())
async def lesson_start_from_callback_processing(
    callback: types.CallbackQuery,
    callback_data: LessonStartsFromCallbackFactory,
    bot: Bot,
    user: User,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    lesson_id = callback_data.lesson_id
    slide_id = callback_data.slide_id
    attr = callback_data.attr

    session = await get_current_session(user.id, lesson_id, db_session)
    lesson = await get_lesson_by_id(lesson_id, db_session)

    if session:
        await update_session_status(session.id, new_status=SessionStatus.ABORTED, db_session=db_session)

    path: list[int] = [int(elem) for elem in lesson.path.split(".")]
    first_exam_slide_id = await find_first_exam_slide_id(path, db_session)

    if attr == LessonStartsFrom.EXAM:
        path_start_index = path.index(first_exam_slide_id)
        path = path[path_start_index:]

    if attr != LessonStartsFrom.CONTINUE:
        session = Session(
            user_id=user.id,
            lesson_id=lesson_id,
            current_slide_id=slide_id if attr != LessonStartsFrom.EXAM else first_exam_slide_id,
            starts_from=lesson_to_session(attr),
            path='.'.join(map(str, path)),
            path_extra=lesson.path_extra,
        )
        db_session.add(session)
        await db_session.flush()

    await lesson_routine(bot, user, slide_id, session, state, db_session)
    await state.update_data(session_id=session.id)
    await callback.answer()


@router.callback_query(RemindersCallbackFactory.filter())
async def reminders_callback_processing(
    callback: types.CallbackQuery,
    callback_data: RemindersCallbackFactory,
    user: User,
    db_session: AsyncSession,
) -> None:
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass
    frequency = callback_data.frequency
    text = await get_text_by_prompt(prompt='set_reminder_message', db_session=db_session)
    if frequency > 0:
        match frequency:
            case 1:
                message = text.format('каждый день')
            case 3:
                message = text.format('каждые 3 дня')
            case 7:
                message = text.format('каждую неделю')
            case _:
                assert False, 'unexpected frequency'
    else:
        message = await get_text_by_prompt(prompt='unset_reminder_message', db_session=db_session)
    await set_user_reminders(
        user_id=user.id, reminder_freq=frequency if frequency > 0 else None, db_session=db_session
    )
    await callback.message.answer(text=message)
    await callback.answer()
    # TODO: вот тут нужен правильный флаг, чтобы после команды не показывать старт меню
    await show_start_menu(user=user, message=callback.message, db_session=db_session)
