import asyncio
from datetime import datetime, timedelta
import logging

from aiogram import Bot, types
from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.lesson_controllers import get_completed_lessons, get_lessons
from bot.database.database_connector import DatabaseConnector
from bot.database.models.user import User
from bot.keyboards.keyboards import get_lesson_picker_keyboard, get_notified_keyboard
from bot.resources.answers import replies
from bot.resources.enums import Times


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


async def propose_reminder_to_user(message: types.Message) -> None:
    await message.answer(
        text=replies["registration_message"],
        reply_markup=get_notified_keyboard(),
    )


async def show_start_menu(user: User, message: types.Message, db_session: AsyncSession) -> None:
    lessons = await get_lessons(db_session)
    completed_lessons = await get_completed_lessons(user_id=user.id, db_session=db_session)
    # TODO: перенести текста в базу
    await message.answer(
        text="<b>Вас приветствует <i>поли-бот</i>!</b>\n",
        reply_markup=get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )


async def get_all_users_with_reminders(db_session: AsyncSession) -> list[User]:
    query = select(User).filter(User.reminder_freq)
    result = await db_session.execute(query)
    return list(result.scalars().all())


async def update_last_reminded_at(user_id: int, timestamp: datetime, db_session: AsyncSession) -> None:
    await db_session.execute(update(User).filter(User.id == user_id).values(last_reminded_at=timestamp))


async def check_user_reminders(bot: Bot, db_connector: DatabaseConnector):
    while True:
        await asyncio.sleep(Times.ONE_HOUR.value)
        utcnow = datetime.utcnow()
        if utcnow.hour == Times.UTC_STARTING_MARK.value:
            async with db_connector.session_factory() as session:
                for user in await get_all_users_with_reminders(session):
                    delta = utcnow - user.last_reminded_at
                    if delta > timedelta(days=user.reminder_freq):
                        logging.info(f"{'=' * 10} {'reminder sended to' + str(user)}")
                        await bot.send_message(chat_id=user.telegram_id, text=replies["reminder_text"])
                        await update_last_reminded_at(user_id=user.id, timestamp=utcnow, db_session=session)
                        await session.commit()
