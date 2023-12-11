from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.session import Session
from bot.database.models.session_log import SessionLog
from bot.resources.enums import CountQuizSlidesMode, SessionStatus, SlideType


async def get_lesson_progress(user_id: int, lesson_id: int, db_session: AsyncSession) -> int:
    query = select(Session.current_slide_id).filter(
        Session.user_id == user_id,
        Session.lesson_id == lesson_id,
        Session.status == SessionStatus.IN_PROGRESS,
    )
    result: Result = await db_session.execute(query)
    user_progress = result.scalar_one_or_none()
    return user_progress


async def get_current_session(user_id: int, lesson_id: int, db_session: AsyncSession) -> Session | None:
    query = select(Session).filter(
        Session.user_id == user_id,
        Session.lesson_id == lesson_id,
        Session.status == SessionStatus.IN_PROGRESS,
    )
    result: Result = await db_session.execute(query)
    return result.scalar_one_or_none()


async def get_session(session_id: int, db_session: AsyncSession) -> Session | None:
    session = await db_session.get(Session, session_id)
    return session


async def update_session_status(session_id: int, new_status: SessionStatus, db_session: AsyncSession) -> None:
    query = update(Session).filter(Session.id == session_id).values(status=new_status)
    await db_session.execute(query)


async def get_wrong_answers_counter(session_id: int, slide_id: int, db_session: AsyncSession) -> int:
    filtered_states = ["continue_button", "/start", "/position", "Далее"]
    query = select(func.count(SessionLog.id)).filter(
        SessionLog.session_id == session_id,
        SessionLog.slide_id == slide_id,
        ~(SessionLog.data.in_(filtered_states)),
        ~SessionLog.is_correct,
    )
    result = await db_session.execute(query)
    return result.scalar()


async def commit_answer_to_db():
    ...
