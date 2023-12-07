from sqlalchemy import Result, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Session
from core.resources.enums import SessionStatus


async def get_lesson_progress(user_id: int, lesson_id: int, db_session: AsyncSession) -> int:
    query = select(Session.current_slide_id).filter(Session.user_id == user_id, Session.lesson_id == lesson_id,
                                                    Session.status == SessionStatus.IN_PROGRESS)
    result: Result = await db_session.execute(query)
    user_progress = result.scalar_one_or_none()
    return user_progress


async def get_current_session(user_id: int, lesson_id: int, db_session: AsyncSession) -> Session | None:
    stmt = select(exists().where(Session.user_id == user_id, Session.lesson_id == lesson_id,
                                 Session.status == SessionStatus.IN_PROGRESS))
    result: Result = await db_session.execute(stmt)
    session_exists = result.scalar()
    if not session_exists:
        return None
    query = select(Session).filter(Session.user_id == user_id, Session.lesson_id == lesson_id,
                                   Session.status == SessionStatus.IN_PROGRESS)
    result: Result = await db_session.execute(query)
    current_session = result.scalar_one_or_none()
    return current_session


async def get_session(session_id: int, db_session: AsyncSession) -> Session | None:
    session = await db_session.get(Session, session_id)
    return session


async def update_session_status(session_id: int, status: SessionStatus, new_status: SessionStatus,
                                db_session: AsyncSession) -> None:
    query = update(Session).filter(Session.id == session_id, Session.status == status).values(status=new_status)
    await db_session.execute(query)

