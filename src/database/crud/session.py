from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.quiz_answer_log import QuizAnswerLog
from database.models.session import Session
from enums import SessionStatus, SlideType


async def get_current_session(user_id: int, lesson_id: int, db_session: AsyncSession) -> Session | None:
    query = select(Session).filter(
        Session.user_id == user_id,
        Session.lesson_id == lesson_id,
        Session.status == SessionStatus.IN_PROGRESS,
    )
    result: Result = await db_session.execute(query)
    return result.scalar_one_or_none()


async def get_last_session_with_progress(user_id: int, db_session: AsyncSession) -> Session | None:
    query = (
        select(Session)
        .filter(
            Session.user_id == user_id,
            Session.status == SessionStatus.IN_PROGRESS,
        )
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    result = await db_session.execute(query)
    last_session = result.scalars().first()
    return last_session


async def get_session(session_id: int, db_session: AsyncSession) -> Session | None:
    session = await db_session.get(Session, session_id)
    return session


async def update_session_status(session_id: int, new_status: SessionStatus, db_session: AsyncSession) -> None:
    query = update(Session).filter(Session.id == session_id).values(status=new_status)
    await db_session.execute(query)


async def get_wrong_answers_counter(session_id: int, slide_id: int, db_session: AsyncSession) -> int:
    query = select(func.count(QuizAnswerLog.id)).filter(
        QuizAnswerLog.session_id == session_id,
        QuizAnswerLog.slide_id == slide_id,
        ~QuizAnswerLog.is_correct,
    )
    result = await db_session.execute(query)
    return result.scalar()


async def get_all_questions_in_session(session_id: int, db_session: AsyncSession) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(QuizAnswerLog.slide_id).filter(
        QuizAnswerLog.session_id == session_id,
        QuizAnswerLog.slide_type.in_(all_questions_slide_types),
    )
    result = await db_session.execute(query)
    return set(result.scalars().all()) if result else {}


async def get_error_counter_from_slides(session_id, slides_set: set[int], db_session: AsyncSession) -> int:
    subquery = (
        select(QuizAnswerLog.slide_id)
        .filter(
            QuizAnswerLog.session_id == session_id,
            QuizAnswerLog.slide_id.in_(slides_set),
            ~QuizAnswerLog.is_correct,
        )
        .distinct()
        .subquery()
    )
    query = select(func.count()).select_from(subquery)
    result = await db_session.execute(query)
    return result.scalar()


async def get_sessions_statistics(
    db_session: AsyncSession,
    status: SessionStatus | None = None,
) -> int:
    query = select(func.count()).select_from(Session)
    if status is not None:
        query = query.filter(Session.status == status)

    result = await db_session.execute(query)
    count = result.scalar_one()
    return count


async def abort_in_progress_sessions_by_lesson(lesson_id: int, db_session: AsyncSession):
    query = (
        update(Session)
        .where((Session.lesson_id == lesson_id) & (Session.status == SessionStatus.IN_PROGRESS))
        .values(status=SessionStatus.ABORTED)
    )
    await db_session.execute(query)
