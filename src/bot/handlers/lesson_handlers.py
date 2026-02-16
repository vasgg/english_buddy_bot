from contextlib import suppress

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.slide_controllers import show_slides
from bot.controllers.user_controllers import show_start_menu
from bot.keyboards.callback_data import LessonStartsFromCallbackFactory, LessonsCallbackFactory, RemindersCallbackFactory
from bot.keyboards.keyboards import get_lesson_progress_keyboard
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import get_lesson_by_id
from database.crud.session import get_current_session, update_session_status
from database.crud.slide import find_first_exam_slide_id
from database.crud.user import set_user_reminders
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.user import User
from enums import LessonStartsFrom, SessionStatus, UserLessonProgress, UserSubscriptionType, lesson_to_session
from lesson_path import LessonPath

router = Router()


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(
    callback: types.CallbackQuery,
    callback_data: LessonsCallbackFactory,
    user: User,
    db_session: AsyncSession,
) -> None:
    with suppress(TelegramBadRequest):
        await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete()

    session = await get_current_session(user_id=user.id, lesson_id=callback_data.lesson_id, db_session=db_session)
    lesson = await get_lesson_by_id(lesson_id=callback_data.lesson_id, db_session=db_session)
    lesson_path = LessonPath(lesson.path).path
    slides_count = len(lesson_path)
    if slides_count == 0:
        await callback.message.answer(text='no slides yet in this lesson')
        return
    first_exam_slide = await find_first_exam_slide_id(lesson_path, db_session)
    has_exam_slides = first_exam_slide is not None
    if lesson.is_paid and user.subscription_status not in (
        UserSubscriptionType.UNLIMITED_ACCESS,
        UserSubscriptionType.LIMITED_ACCESS,
    ):
        await callback.message.answer(text=await get_text_by_prompt(prompt='paywall_message', db_session=db_session))
        return
    if session:
        await callback.message.answer(
            text=await get_text_by_prompt(prompt='starts_from_with_progress', db_session=db_session),
            reply_markup=await get_lesson_progress_keyboard(
                mode=UserLessonProgress.IN_PROGRESS,
                lesson=lesson,
                has_exam_slides=has_exam_slides,
            ),
        )
    else:
        prompt = 'starts_from_with_exam' if has_exam_slides else 'starts_from_without_exam'
        text = await get_text_by_prompt(prompt=prompt, db_session=db_session)
        await callback.message.answer(
            text=text,
            reply_markup=await get_lesson_progress_keyboard(
                mode=UserLessonProgress.NO_PROGRESS,
                lesson=lesson,
                has_exam_slides=has_exam_slides,
            ),
        )


async def prepare_session(lesson: Lesson, db_session: AsyncSession, attr: LessonStartsFrom, user_id: int) -> Session:
    path = lesson.path
    if attr == LessonStartsFrom.EXAM:
        path_list = LessonPath(path).path
        first_exam_slide_id = await find_first_exam_slide_id(path_list, db_session)
        if first_exam_slide_id:
            path_start_index = path_list.index(first_exam_slide_id)
            path = '.'.join(map(str, path_list[path_start_index:]))

    session = Session(
        user_id=user_id,
        lesson_id=lesson.id,
        starts_from=lesson_to_session(attr),
        path=path,
        path_extra=lesson.path_extra,
    )
    db_session.add(session)
    await db_session.flush()
    return session


@router.callback_query(LessonStartsFromCallbackFactory.filter())
async def lesson_start_from_callback_processing(
    callback: types.CallbackQuery,
    callback_data: LessonStartsFromCallbackFactory,
    user: User,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    with suppress(TelegramBadRequest):
        await callback.answer()
    with suppress(TelegramBadRequest, AttributeError):
        await callback.message.delete()

    lesson_id = callback_data.lesson_id
    attr = callback_data.attr

    session = await get_current_session(user.id, lesson_id, db_session)
    lesson = await get_lesson_by_id(lesson_id, db_session)

    if attr != LessonStartsFrom.CONTINUE:
        if session:
            await update_session_status(session.id, new_status=SessionStatus.ABORTED, db_session=db_session)

        session = await prepare_session(lesson, db_session, attr, user.id)

    await show_slides(callback.message, state, session, db_session)
    await state.update_data(session_id=session.id)


@router.callback_query(RemindersCallbackFactory.filter())
async def reminders_callback_processing(
    callback: types.CallbackQuery,
    callback_data: RemindersCallbackFactory,
    user: User,
    db_session: AsyncSession,
) -> None:
    with suppress(TelegramBadRequest):
        await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete()

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
                raise AssertionError('unexpected frequency')
    else:
        message = await get_text_by_prompt(prompt='unset_reminder_message', db_session=db_session)
    await set_user_reminders(user_id=user.id, reminder_freq=frequency if frequency > 0 else None, db_session=db_session)
    await db_session.commit()
    await callback.message.answer(text=message)
    # TODO: вот тут нужен правильный флаг, чтобы после команды не показывать старт меню
    await show_start_menu(event=callback.message, user_id=user.id, db_session=db_session)
