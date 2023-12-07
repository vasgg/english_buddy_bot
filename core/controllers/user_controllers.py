from sqlalchemy import Result, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Session
from core.database.models.user import User
from core.resources.enums import SessionStatus, SessonStartsFrom


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


async def get_user_from_db(event, db_session) -> User:
    query = select(User).filter(User.telegram_id == event.from_user.id)
    result: Result = await db_session.execute(query)
    user = result.scalar()
    if not user:
        user = await add_user_to_db(event, db_session)
    return user


# async def mark_lesson_as_completed(user_id: int, lesson_id: int, db_session: AsyncSession) -> None:
#     query = update(Session).filter(Session.user_id == user_id, Session.lesson_id == lesson_id).values(status=SessionStatus.COMPLETED)
#     await db_session.execute(query)


# async def update_user_progress(user_id: int, lesson_id: int, current_slide: int, session: AsyncSession) -> None:
#     upsert_query = insert(UserProgress).values(user_id=user_id, current_lesson=lesson_id, current_slide=current_slide)
#     upsert_query = upsert_query.on_conflict_do_update(set_={UserProgress.current_slide: current_slide})
#     await session.execute(upsert_query)


async def update_session(user_id: int, lesson_id: int, current_slide_id: int, db_session: AsyncSession,
                         session_id: int, starts_from: SessonStartsFrom = SessonStartsFrom.BEGIN) -> None:
    query = update(Session).filter(Session.user_id == user_id,
                                   Session.lesson_id == lesson_id,
                                   Session.id == session_id).values(current_slide_id=current_slide_id,
                                                                    starts_from=starts_from)
    await db_session.execute(query)
    # query = select(Session).filter(Session.user_id == user_id,
    #                                Session.lesson_id == lesson_id,
    #                                Session.status == SessionStatus.IN_PROGRESS)
    # result: Result = await db_session.execute(query)
    # current_session = result.scalar()
    # if not current_session:
    #     new_session = Session(
    #         user_id=user_id,
    #         lesson_id=lesson_id,
    #         current_slide_id=current_slide_id,
    #         starts_from=starts_from,
    #         status=SessionStatus.IN_PROGRESS
    #     )
    #     db_session.add(new_session)
    # else:
    #     current_session.current_slide_id = current_slide_id
    #     await db_session.flush()
    # upsert_query = insert(Session).values(user_id=user_id, lesson_id=lesson_id, current_slide_id=current_slide_id, starts_from=starts_from)
    # upsert_query = upsert_query.on_conflict_do_update(set_={Session.current_slide_id: current_slide_id})
    # await session.execute(upsert_query)

