from sqlalchemy import Result, delete, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import UserProgress
from core.database.models.user import User


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


async def delete_user_progress(user_id: int, lesson_number: int, session: AsyncSession) -> None:
    query = delete(UserProgress).filter(UserProgress.user_id == user_id,
                                        UserProgress.current_lesson == lesson_number)
    await session.execute(query)


async def update_user_progress(user_id: int, lesson_number: int, session: AsyncSession, current_slide: int) -> None:
    upsert_query = insert(UserProgress).values(user_id=user_id, current_lesson=lesson_number, current_slide=current_slide)
    upsert_query = upsert_query.on_conflict_do_update(set_={UserProgress.current_slide: current_slide})
    await session.execute(upsert_query)


async def get_lesson_progress(user_id: int, lesson_number: int, session: AsyncSession) -> UserProgress.current_slide:
    query = select(UserProgress.current_slide).filter(UserProgress.user_id == user_id,
                                                      UserProgress.current_lesson == lesson_number)
    result: Result = await session.execute(query)
    user_progress = result.scalar()
    return user_progress


async def increment_wrong_attempts_counter(user_id: int, lesson_number: int, session: AsyncSession) -> None:

    upsert_query = insert(UserProgress).values(user_id=user_id, current_lesson=lesson_number, wrong_answer_attempts=1)
    upsert_query.on_conflict_do_update(index_elements=['user_id', 'current_lesson'],
                                       set_=dict(wrong_answer_attempts=UserProgress.wrong_answer_attempts + 1))
    await session.execute(upsert_query)
