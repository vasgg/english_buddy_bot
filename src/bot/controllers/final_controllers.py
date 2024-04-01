import logging

from aiogram import types
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.user_controllers import show_start_menu
from bot.handlers.lesson_handlers import find_first_exam_slide_id
from bot.keyboards.keyboards import (
    get_lesson_picker_keyboard,
    get_extra_slides_keyboard,
)
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import (
    add_completed_lesson_to_db,
    get_all_exam_slides_id_in_lesson,
    get_completed_lessons,
    get_lesson_by_id,
    get_lessons,
)
from database.crud.session import (
    count_errors_in_session,
    get_all_questions_in_session,
    update_session_status,
)
from database.crud.user import get_user_from_db
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from enums import SessionStartsFrom, SessionStatus, SlideType

logger = logging.Logger(__name__)


class UserStats(BaseModel):
    regular_exercises: int | None
    exam_exercises: int | None
    correct_regular_answers: int | None
    correct_exam_answers: int | None


async def get_all_base_questions_id_in_lesson(
    lesson_id: int, exam_slides_id: set[int], db_session: AsyncSession
) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.lesson_id == lesson_id, Slide.slide_type.in_(all_questions_slide_types), ~Slide.id.in_(exam_slides_id)
    )
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()} if result else {}


async def calculate_user_stats(session: Session, db_session: AsyncSession) -> UserStats:
    all_exam_slides_in_lesson = await get_all_exam_slides_id_in_lesson(
        lesson_id=session.lesson_id, db_session=db_session
    )
    all_questions_slides_in_session = await get_all_questions_in_session(session_id=session.id, db_session=db_session)
    total_exam_questions_in_session = all_exam_slides_in_lesson & all_questions_slides_in_session
    total_exam_questions_errors = await count_errors_in_session(
        session_id=session.id, slides_set=total_exam_questions_in_session, db_session=db_session
    )
    total_base_questions_in_lesson = await get_all_base_questions_id_in_lesson(
        lesson_id=session.lesson_id, exam_slides_id=all_exam_slides_in_lesson, db_session=db_session
    )
    total_base_questions_in_session = total_base_questions_in_lesson & all_questions_slides_in_session
    total_base_questions_errors = await count_errors_in_session(
        session_id=session.id, slides_set=total_base_questions_in_lesson, db_session=db_session
    )
    stats = UserStats(
        regular_exercises=len(total_base_questions_in_session),
        exam_exercises=len(total_exam_questions_in_session),
        correct_regular_answers=len(total_base_questions_in_session) - total_base_questions_errors,
        correct_exam_answers=len(total_exam_questions_in_session) - total_exam_questions_errors,
    )
    return stats


async def show_stats(
    event: types.Message, stats: UserStats, state: FSMContext, session: Session, db_session: AsyncSession
) -> None:
    lesson = await get_lesson_by_id(lesson_id=session.lesson_id, db_session=db_session)
    lessons = await get_lessons(db_session)
    exam_slide_id = await find_first_exam_slide_id(session.get_path(), db_session)
    completed_lessons = await get_completed_lessons(user_id=event.from_user.id, db_session=db_session)
    lesson_picker_kb = get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons)
    match session.starts_from:
        case SessionStartsFrom.BEGIN:
            if not exam_slide_id:
                await event.answer(
                    text=(
                        await get_text_by_prompt(prompt='final_report_without_questions', db_session=db_session)
                    ).format(lesson.title),
                    reply_markup=lesson_picker_kb,
                )
                await state.clear()
                return
            await event.answer(
                text=(await get_text_by_prompt(prompt='final_report_from_begin', db_session=db_session)).format(
                    lesson.title,
                    stats.correct_regular_answers,
                    stats.regular_exercises,
                    stats.correct_exam_answers,
                    stats.exam_exercises,
                ),
                reply_markup=lesson_picker_kb,
            )
        case SessionStartsFrom.EXAM:
            await event.answer(
                text=(await get_text_by_prompt(prompt='final_report_from_exam', db_session=db_session)).format(
                    lesson.title,
                    stats.correct_exam_answers,
                    stats.exam_exercises,
                ),
                reply_markup=lesson_picker_kb,
            )
        case _:
            assert False, f'Unexpected session starts from: {session.starts_from}'


async def finish_session(user_id: int, session: Session, db_session: AsyncSession) -> None:
    await add_completed_lesson_to_db(user_id, session.lesson_id, session.id, db_session)
    await update_session_status(
        session_id=session.id,
        new_status=SessionStatus.COMPLETED,
        db_session=db_session,
    )


async def show_extra_slides_dialog(
    event: types.Message,
    db_session: AsyncSession,
) -> None:
    await event.answer(
        text=(await get_text_by_prompt(prompt='extra_slides_dialog', db_session=db_session)),
        reply_markup=get_extra_slides_keyboard(),
    )


async def finalizing(event: types.Message, state: FSMContext, session: Session, db_session: AsyncSession):
    await event.bot.unpin_all_chat_messages(chat_id=event.from_user.id)
    user_stats: UserStats = await calculate_user_stats(session, db_session)
    await show_stats(event, user_stats, state, session, db_session)
    lesson: Lesson = await get_lesson_by_id(session.lesson_id, db_session)
    if lesson.errors_threshold is not None:
        percentage = (user_stats.correct_exam_answers / user_stats.exam_exercises) * 100
        if percentage < lesson.errors_threshold:
            await show_extra_slides_dialog(event, db_session)
            return
    user = await get_user_from_db(event.from_user.id, db_session)
    await finish_session(user.id, session, db_session)
    await show_start_menu(event, db_session)
    await state.clear()


async def finalizing_extra() -> None:
    pass
