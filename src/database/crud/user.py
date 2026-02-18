from datetime import datetime, timedelta, timezone

from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from consts import UTC_STARTING_MARK
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


async def get_user_from_db_by_tg_id(telegram_id: int, db_session: AsyncSession) -> User | None:
    query = select(User).filter(User.telegram_id == telegram_id)
    result: Result = await db_session.execute(query)
    user = result.scalar()
    if user:
        user.last_reminded_at = _ensure_utc(user.last_reminded_at)
    return user


async def get_user_from_db_by_id(user_id: int, db_session: AsyncSession) -> User:
    query = select(User).filter(User.id == user_id)
    result: Result = await db_session.execute(query)
    user = result.scalar()
    user.last_reminded_at = _ensure_utc(user.last_reminded_at)
    return user


def _get_previous_reminder_slot(utcnow: datetime) -> datetime:
    if utcnow.tzinfo is None:
        utcnow = utcnow.replace(tzinfo=timezone.utc)
    slot_today = utcnow.replace(hour=UTC_STARTING_MARK, minute=0, second=0, microsecond=0)
    if utcnow < slot_today:
        slot_today -= timedelta(days=1)
    return slot_today


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def set_user_reminders(user_id: int, reminder_freq: int | None, db_session: AsyncSession) -> None:
    values = {"reminder_freq": reminder_freq}
    if reminder_freq is not None:
        values["last_reminded_at"] = _get_previous_reminder_slot(datetime.now(timezone.utc))
    await db_session.execute(update(User).filter(User.id == user_id).values(**values))


async def get_all_users_with_reminders(db_session: AsyncSession) -> list[User]:
    query = select(User).filter(User.reminder_freq.is_not(None))
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def get_all_users(db_session: AsyncSession) -> list[User]:
    query = select(User)
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def get_all_users_with_active_subscription(db_session: AsyncSession) -> list[User]:
    query = select(User).filter(User.subscription_status == UserSubscriptionType.LIMITED_ACCESS)
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def update_last_reminded_at(user_id: int, timestamp: datetime, db_session: AsyncSession) -> None:
    await db_session.execute(update(User).filter(User.id == user_id).values(last_reminded_at=timestamp))


async def set_subscription_status(
    user_id: int,
    new_status: UserSubscriptionType,
    db_session: AsyncSession,
) -> None:
    await db_session.execute(update(User).filter(User.id == user_id).values(subscription_status=new_status))


async def get_users_count(db_session: AsyncSession) -> int:
    query = select(func.count()).select_from(User)
    result = await db_session.execute(query)
    return result.scalar()
