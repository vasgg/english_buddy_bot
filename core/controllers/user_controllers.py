from sqlalchemy import Result, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Session
from core.database.models.user import User
from core.resources.enums import SessionStartsFrom


async def add_user_to_db(event, db_session) -> User:
    new_user = User(
        telegram_id=event.from_user.id,
        first_name=event.from_user.first_name,
        last_name=event.from_user.last_name,
        username=event.from_user.username,
    )
    db_session.add(new_user)
    await db_session.flush()
    return new_user


async def get_user_from_db(event, db_session: AsyncSession) -> User:
    query = select(User).filter(User.telegram_id == event.from_user.id)
    result: Result = await db_session.execute(query)
    user = result.scalar()
    if not user:
        user = await add_user_to_db(event, db_session)
    return user


async def update_session(
    user_id: int,
    lesson_id: int,
    current_slide_id: int,
    db_session: AsyncSession,
    session_id: int,
) -> None:
    query = (
        update(Session)
        .filter(
            Session.user_id == user_id,
            Session.lesson_id == lesson_id,
            Session.id == session_id,
        )
        .values(current_slide_id=current_slide_id)
    )
    await db_session.execute(query)
