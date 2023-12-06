from sqlalchemy import select, Result
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Session
from core.resources.enums import SessionStatus


async def get_lesson_progress(user_id: int, lesson_id: int, session: AsyncSession) -> int:
    query = select(Session.current_slide_id).filter(Session.user_id == user_id, Session.lesson_id == lesson_id, Session.status == SessionStatus.IN_PROGRESS)
    result: Result = await session.execute(query)
    user_progress = result.scalar_one_or_none()
    return user_progress


async def get_current_session(user_id: int, lesson_id: int, session: AsyncSession) -> Session:
    query = select(Session).filter(Session.user_id == user_id, Session.lesson_id == lesson_id,
                                                    Session.status == SessionStatus.IN_PROGRESS)
    result: Result = await session.execute(query)
    return result.scalar()
