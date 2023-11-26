from sqlalchemy import Result, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import UserProgress
from core.database.models.user import User


async def create_user_in_db(event, session) -> User:
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
        user = await create_user_in_db(event, session)
    return user


async def get_user_progress(user_id: int, lesson_number: int, session: AsyncSession, slide_number: int = None) -> UserProgress.current_slide:
    query = select(UserProgress).filter(UserProgress.user_id == user_id, UserProgress.current_lesson == lesson_number)
    result: Result = await session.execute(query)
    user_progress = result.scalar()
    if not user_progress:
        user_progress = UserProgress(user_id=user_id, current_lesson=lesson_number)
        session.add(user_progress)
        await session.flush()
    # TODO: разнести на 2 функции
    if user_progress.current_slide < slide_number:
        user_progress.current_slide = slide_number
        await session.flush()
    return user_progress.current_slide
