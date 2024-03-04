from datetime import datetime

from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User


async def add_user_to_db(event, db_session) -> User:
    new_user = User(
        telegram_id=event.from_user.id,
        first_name=event.from_user.first_name,
        last_name=event.from_user.last_name,
        username=event.from_user.username,
        paywall_access=False,
        reminder_freq=None,
        last_reminded_at=datetime.utcnow(),
    )
    db_session.add(new_user)
    await db_session.flush()
    return new_user


async def get_user_from_db(event, db_session: AsyncSession) -> User:
    query = select(User).filter(User.telegram_id == event.from_user.id)
    result: Result = await db_session.execute(query)
    user = result.scalar()
    return user


async def toggle_user_paywall_access(user_id: int, db_session: AsyncSession) -> None:
    await db_session.execute(
        update(User).filter(User.id == user_id).values(paywall_access=func.not_(User.paywall_access))
    )


async def set_user_reminders(user_id: int, reminder_freq: int, db_session: AsyncSession) -> None:
    await db_session.execute(update(User).filter(User.id == user_id).values(reminder_freq=reminder_freq))


async def get_all_users_with_reminders(db_session: AsyncSession) -> list[User]:
    query = select(User).filter(User.reminder_freq)
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def update_last_reminded_at(user_id: int, timestamp: datetime, db_session: AsyncSession) -> None:
    await db_session.execute(update(User).filter(User.id == user_id).values(last_reminded_at=timestamp))
