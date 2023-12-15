from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.lesson_controllers import get_lesson, lesson_routine
from bot.controllers.session_controller import get_current_session, update_session, update_session_status
from bot.controllers.user_controllers import set_user_reminders, show_start_menu
from bot.database.models.session import Session
from bot.database.models.user import User
from bot.keyboards.callback_builders import (
    LessonStartsFromCallbackFactory,
    LessonsCallbackFactory,
    RemindersCallbackFactory,
)
from bot.keyboards.keyboards import get_lesson_progress_keyboard
from bot.resources.answers import replies
from bot.resources.enums import (
    LessonStartsFrom,
    SessionStatus,
    UserLessonProgress,
    lesson_to_session,
)

router = Router()


async def common_processing(
    bot: Bot,
    user: User,
    lesson_id: int,
    slide_id: int,
    session: Session,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    await update_session(
        user.id,
        lesson_id,
        current_slide_id=slide_id,
        session_id=session.id,
        db_session=db_session,
    )
    await lesson_routine(bot, user, lesson_id, slide_id, state, session.id, db_session)


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(
    callback: types.CallbackQuery,
    callback_data: LessonsCallbackFactory,
    user: User,
    db_session: AsyncSession,
) -> None:
    await callback.message.delete()
    session = await get_current_session(user_id=user.id, lesson_id=callback_data.lesson_id, db_session=db_session)
    lesson = await get_lesson(lesson_id=callback_data.lesson_id, db_session=db_session)
    if lesson.is_paid and user.paywall_access is False:
        await callback.message.answer(text=replies["paywall_message"])
        return
    if session:
        await callback.message.answer(
            text="Вы можете продолжить урок, или начать его сначала.",
            reply_markup=await get_lesson_progress_keyboard(
                mode=UserLessonProgress.IN_PROGRESS,
                lesson=lesson,
                current_slide_id=session.current_slide_id,
            ),
        )
    else:
        if lesson.exam_slide_id:
            await callback.message.answer(
                text="Вы можете начать урок сначала, или сразу перейти к экзамену.",
                reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.NO_PROGRESS, lesson=lesson),
            )
        else:
            await callback.message.answer(
                text="В этом уроке нет экзамена, его можно пройти только сначала.",
                reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.NO_PROGRESS, lesson=lesson),
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
    await callback.message.delete()
    lesson_id = callback_data.lesson_id
    slide_id = callback_data.slide_id
    attr = callback_data.attr
    session = await get_current_session(user.id, lesson_id, db_session)
    match attr:
        case LessonStartsFrom.BEGIN | LessonStartsFrom.EXAM:
            if session:
                await update_session_status(session.id, new_status=SessionStatus.ABORTED, db_session=db_session)
            session = Session(
                user_id=user.id,
                lesson_id=lesson_id,
                current_slide_id=slide_id,
                starts_from=lesson_to_session(attr),
            )
            db_session.add(session)
            await db_session.flush()
        case LessonStartsFrom.CONTINUE:
            pass
        case _:
            assert False, "invalid attr"

    await common_processing(bot, user, lesson_id, slide_id, session, state, db_session)
    await state.update_data(session_id=session.id)
    await callback.answer()


@router.callback_query(RemindersCallbackFactory.filter())
async def reminders_callback_processing(
    callback: types.CallbackQuery,
    callback_data: RemindersCallbackFactory,
    user: User,
    db_session: AsyncSession,
) -> None:
    await callback.message.delete()
    frequency = callback_data.frequency
    if frequency > 0:
        match frequency:
            case 1:
                text = replies["set_reminder_message"].format("каждый день")
            case 3:
                text = replies["set_reminder_message"].format("каждые 3 дня")
            case 7:
                text = replies["set_reminder_message"].format("каждую неделю")
            case _:
                assert False, "unexpected frequency"
    else:
        text = replies["unset_reminder_message"]
    await set_user_reminders(user_id=user.id, reminder_freq=frequency, db_session=db_session)
    await callback.message.answer(text=text)
    await callback.answer()
    # TODO: вот тут нужен правильный флаг, чтобы после команды не показывать старт меню
    await show_start_menu(user=user, message=callback.message, db_session=db_session)
