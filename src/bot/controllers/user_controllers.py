import asyncio
from datetime import datetime, timedelta
import logging

from aiogram import Bot, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.keyboards import get_lesson_picker_keyboard, get_notified_keyboard
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import get_completed_lessons, get_lessons
from database.crud.user import get_all_users_with_reminders, update_last_reminded_at
from database.database_connector import DatabaseConnector

logger = logging.getLogger()
UTC_STARTING_MARK = 14
ONE_HOUR = 3600


async def propose_reminder_to_user(message: types.Message, db_session: AsyncSession) -> None:
    await message.answer(
        text=await get_text_by_prompt(prompt='registration_message', db_session=db_session),
        reply_markup=get_notified_keyboard(),
    )


async def show_start_menu(event: types.Message, db_session: AsyncSession) -> None:
    lessons = await get_lessons(db_session)
    completed_lessons = await get_completed_lessons(user_id=event.from_user.id, db_session=db_session)
    await event.answer(
        text=await get_text_by_prompt(prompt='start_message', db_session=db_session),
        reply_markup=get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )


async def check_user_reminders(bot: Bot, db_connector: DatabaseConnector):
    while True:
        await asyncio.sleep(ONE_HOUR)
        utcnow = datetime.utcnow()
        if utcnow.hour == UTC_STARTING_MARK - 1:
            await asyncio.sleep(ONE_HOUR - utcnow.minute * 60 - utcnow.second)
            async with db_connector.session_factory() as session:
                for user in await get_all_users_with_reminders(session):
                    delta = datetime.utcnow() - user.last_reminded_at
                    if delta > timedelta(days=user.reminder_freq):
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=await get_text_by_prompt(prompt='reminder_text', db_session=session),
                        )
                        logger.info(f"{'reminder sended to ' + str(user)}")
                        await update_last_reminded_at(user_id=user.id, timestamp=datetime.utcnow(), db_session=session)
                        await session.commit()
