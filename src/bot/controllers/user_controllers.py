from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.session import Session
from bot.database.models.user import User
from bot.keyboards.keyboards import get_notified_keyboard


async def add_user_to_db(event, db_session) -> User:
    new_user = User(
        telegram_id=event.from_user.id,
        first_name=event.from_user.first_name,
        last_name=event.from_user.last_name,
        username=event.from_user.username,
        paywall_access=False,
        reminder_freq=None,
    )
    db_session.add(new_user)
    await db_session.flush()
    await event.bot.send_message(
        chat_id=event.from_user.id,
        text="Вы успешно зарегистрированы в боте. Хотите включить автоматические напоминания о занятиях?",
        reply_markup=get_notified_keyboard(),
    )
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


async def toggle_user_paywall_access(user_id: int, db_session: AsyncSession) -> None:
    await db_session.execute(
        update(User).filter(User.id == user_id).values(paywall_access=func.not_(User.paywall_access))
    )
