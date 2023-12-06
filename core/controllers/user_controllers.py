from sqlalchemy import Result, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Session
from core.database.models.user import User
from core.resources.enums import SessionStatus, StartsFrom


async def add_user_to_db(event, session) -> User:
    new_user = User(
        telegram_id=event.from_user.id,
        first_name=event.from_user.first_name,
        last_name=event.from_user.last_name,
        username=event.from_user.username,
    )
    session.add(new_user)
    await session.flush()
    return new_user


async def get_user_from_db(event, session) -> User:
    query = select(User).filter(User.telegram_id == event.from_user.id)
    result: Result = await session.execute(query)
    user = result.scalar()
    if not user:
        user = await add_user_to_db(event, session)
    return user


async def mark_lesson_as_completed(user_id: int, lesson_id: int, session: AsyncSession) -> None:
    query = update(Session).filter(Session.user_id == user_id, Session.lesson_id == lesson_id).values(status=SessionStatus.COMPLETED)
    await session.execute(query)


# async def update_user_progress(user_id: int, lesson_id: int, current_slide: int, session: AsyncSession) -> None:
#     upsert_query = insert(UserProgress).values(user_id=user_id, current_lesson=lesson_id, current_slide=current_slide)
#     upsert_query = upsert_query.on_conflict_do_update(set_={UserProgress.current_slide: current_slide})
#     await session.execute(upsert_query)


async def update_session(user_id: int, lesson_id: int, current_slide_id: int, session: AsyncSession,
                         starts_from: StartsFrom = StartsFrom.BEGIN) -> None:
    query = select(Session).filter(Session.user_id == user_id,
                                   Session.lesson_id == lesson_id,
                                   Session.status == SessionStatus.IN_PROGRESS)
    result: Result = await session.execute(query)
    current_session = result.scalar()
    if not current_session:
        new_session = Session(
            user_id=user_id,
            lesson_id=lesson_id,
            current_slide_id=current_slide_id,
            starts_from=starts_from,
            status=SessionStatus.IN_PROGRESS
        )
        session.add(new_session)
    else:
        current_session.current_slide_id = current_slide_id
        await session.flush()
    # upsert_query = insert(Session).values(user_id=user_id, lesson_id=lesson_id, current_slide_id=current_slide_id, starts_from=starts_from)
    # upsert_query = upsert_query.on_conflict_do_update(set_={Session.current_slide_id: current_slide_id})
    # await session.execute(upsert_query)


async def get_lesson_progress(user_id: int, lesson_id: int, session: AsyncSession) -> Session.current_slide_id:
    query = select(Session.current_slide_id).filter(Session.user_id == user_id, Session.lesson_id == lesson_id, Session.id == ...)
    result: Result = await session.execute(query)
    user_progress = result.scalar()
    return user_progress
