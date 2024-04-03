import logging
from typing import TYPE_CHECKING

from aiogram import types
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.keyboards import (
    get_extra_slides_keyboard,
    get_lesson_picker_keyboard,
)
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import (
    get_completed_lessons_from_sessions,
    get_lesson_by_id,
    get_lessons,
)
from database.crud.session import (
    get_error_counter_from_slides,
    update_session_status,
)
from database.crud.slide import find_first_exam_slide_id
from database.models.session import Session
from enums import SessionStartsFrom, SessionStatus

if TYPE_CHECKING:
    from database.models.lesson import Lesson

logger = logging.Logger(__name__)


class StatsCalculationResults(BaseModel):
    exercises: int
    correct_answers: int


class UserStats(BaseModel):
    regular_exercises: int | None
    exam_exercises: int | None = None
    correct_regular_answers: int | None
    correct_exam_answers: int | None = None


async def calculate_user_stats_from_slides(
    slides: set[int], session_id: int, db_session: AsyncSession
) -> StatsCalculationResults:
    all_right_answers_in_slides = len(slides) - await get_error_counter_from_slides(
        session_id=session_id, slides_set=slides, db_session=db_session
    )
    stats = StatsCalculationResults(
        exercises=len(slides),
        correct_answers=all_right_answers_in_slides,
    )
    return stats


async def show_stats(
    event: types.Message,
    stats: UserStats,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
    markup: types.InlineKeyboardMarkup | None = None,
) -> None:
    lesson = await get_lesson_by_id(lesson_id=session.lesson_id, db_session=db_session)
    exam_slide_id = await find_first_exam_slide_id(session.get_path(), db_session)
    match session.starts_from:
        case SessionStartsFrom.BEGIN:
            if not exam_slide_id:
                await event.answer(
                    text=(await get_text_by_prompt(prompt='final_report_without_questions', db_session=db_session)).format(
                        lesson.title
                    ),
                    reply_markup=markup,
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
                reply_markup=markup,
            )
        case SessionStartsFrom.EXAM:
            await event.answer(
                text=(await get_text_by_prompt(prompt='final_report_from_exam', db_session=db_session)).format(
                    lesson.title,
                    stats.correct_exam_answers,
                    stats.exam_exercises,
                ),
                reply_markup=markup,
            )
        case _:
            msg = f'Unexpected session starts from: {session.starts_from}'
            raise AssertionError(msg)


async def show_stats_extra(
    event: types.Message,
    stats: StatsCalculationResults,
    session: Session,
    db_session: AsyncSession,
) -> None:
    lesson = await get_lesson_by_id(lesson_id=session.lesson_id, db_session=db_session)
    lessons = await get_lessons(db_session)
    completed_lessons = await get_completed_lessons_from_sessions(user_id=session.user_id, db_session=db_session)
    lesson_picker_kb = get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons)
    await event.answer(
        text=(await get_text_by_prompt(prompt='final_report_extra', db_session=db_session)).format(
            lesson.title,
            stats.correct_answers,
            stats.exercises,
        ),
        reply_markup=lesson_picker_kb,
    )


async def finish_session(session: Session, db_session: AsyncSession) -> None:
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
    slides_ids = session.get_path()
    first_exam_slide_id = await find_first_exam_slide_id(slides_ids, db_session)
    first_exam_slide_index = slides_ids.index(first_exam_slide_id)
    regular_quiz_slides = slides_ids[:first_exam_slide_index]
    exam_quiz_slides = slides_ids[first_exam_slide_index:]
    results_regular = await calculate_user_stats_from_slides(regular_quiz_slides, session.id, db_session)
    results_exam = await calculate_user_stats_from_slides(exam_quiz_slides, session.id, db_session)
    user_stats = UserStats(
        regular_exercises=len(regular_quiz_slides),
        exam_exercises=len(exam_quiz_slides),
        correct_regular_answers=results_regular.correct_answers,
        correct_exam_answers=results_exam.correct_answers,
    )
    lesson: Lesson = await get_lesson_by_id(session.lesson_id, db_session)
    if lesson.errors_threshold is not None:
        percentage = (user_stats.correct_exam_answers / user_stats.exam_exercises) * 100
        if percentage < lesson.errors_threshold:
            await show_stats(event, user_stats, state, session, db_session)
            await show_extra_slides_dialog(event, db_session)
            return
    lessons = await get_lessons(db_session)
    completed_lessons = await get_completed_lessons_from_sessions(user_id=session.user_id, db_session=db_session)
    markup = get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons)
    await show_stats(event, user_stats, state, session, db_session, markup=markup)
    await finish_session(session, db_session)
    await state.clear()


async def finalizing_extra(event: types.Message, state: FSMContext, session: Session, db_session: AsyncSession):
    slides_ids = session.get_path()
    first_exam_slide_id = await find_first_exam_slide_id(slides_ids, db_session)
    first_exam_slide_index = slides_ids.index(first_exam_slide_id)
    regular_quiz_slides = slides_ids[:first_exam_slide_index]
    results_regular = await calculate_user_stats_from_slides(regular_quiz_slides, session.id, db_session)
    await show_stats_extra(event, results_regular, session, db_session)
    await finish_session(session, db_session)
    await state.clear()
