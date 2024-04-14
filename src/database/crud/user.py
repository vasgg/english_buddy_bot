from datetime import datetime, timezone

from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from enums import UserSubscriptionType


async def add_user_to_db(user, db_session) -> User:
    new_user = User(
        telegram_id=user.id,
        fullname=user.full_name,
        username=user.username,
        last_reminded_at=datetime.now(timezone.utc),
    )
    db_session.add(new_user)
    await db_session.flush()
    return new_user


async def get_user_from_db_by_tg_id(telegram_id: int, db_session: AsyncSession) -> User:
    query = select(User).filter(User.telegram_id == telegram_id)
    result: Result = await db_session.execute(query)
    user = result.scalar()
    user.last_reminded_at = user.last_reminded_at.replace(tzinfo=timezone.utc)
    return user


async def get_user_from_db_by_id(user_id: int, db_session: AsyncSession) -> User:
    query = select(User).filter(User.id == user_id)
    result: Result = await db_session.execute(query)
    user = result.scalar()
    user.last_reminded_at = user.last_reminded_at.replace(tzinfo=timezone.utc)
    return user


async def set_user_reminders(user_id: int, reminder_freq: int, db_session: AsyncSession) -> None:
    await db_session.execute(update(User).filter(User.id == user_id).values(reminder_freq=reminder_freq))


async def get_all_users_with_reminders(db_session: AsyncSession) -> list[User]:
    query = select(User).filter(User.reminder_freq)
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def get_all_users_with_active_subscription(db_session: AsyncSession) -> list[User]:
    query = select(User).filter(User.subscription_status == UserSubscriptionType.LIMITED_ACCESS)
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def update_last_reminded_at(user_id: int, timestamp: datetime, db_session: AsyncSession) -> None:
    await db_session.execute(update(User).filter(User.id == user_id).values(last_reminded_at=timestamp))


async def get_users_count(db_session: AsyncSession) -> int:
    query = select(func.count()).select_from(User)
    result = await db_session.execute(query)
    return result.scalar()
