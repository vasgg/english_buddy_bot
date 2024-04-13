import asyncio
from datetime import datetime, timedelta, timezone
import logging

from aiogram import Bot, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.keyboards import get_lesson_picker_keyboard, get_notified_keyboard, get_premium_keyboard
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import get_completed_lessons_from_sessions, get_lessons
from database.crud.user import get_all_users_with_active_subscription, get_all_users_with_reminders, update_last_reminded_at
from database.database_connector import DatabaseConnector
from enums import UserSubscriptionType

logger = logging.getLogger()
UTC_STARTING_MARK = 14
ONE_HOUR = 3600
ONE_DAY = 86400


async def propose_reminder_to_user(message: types.Message, db_session: AsyncSession) -> None:
    await message.answer(
        text=await get_text_by_prompt(prompt='registration_message', db_session=db_session),
        reply_markup=get_notified_keyboard(),
    )


async def show_start_menu(event: types.Message, user_id: int, db_session: AsyncSession) -> None:
    lessons = await get_lessons(db_session)
    completed_lessons = await get_completed_lessons_from_sessions(user_id=user_id, db_session=db_session)
    await event.answer(
        text=await get_text_by_prompt(prompt='start_message', db_session=db_session),
        reply_markup=get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )


async def check_user_reminders(bot: Bot, db_connector: DatabaseConnector):
    while True:
        await asyncio.sleep(ONE_HOUR)
        utcnow = datetime.now(timezone.utc)
        if utcnow.hour == UTC_STARTING_MARK - 1:
            await asyncio.sleep(ONE_HOUR - utcnow.minute * 60 - utcnow.second)
            async with db_connector.session_factory() as session:
                for user in await get_all_users_with_reminders(session):
                    delta = datetime.now(timezone.utc) - user.last_reminded_at
                    if delta > timedelta(days=user.reminder_freq):
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=await get_text_by_prompt(prompt='reminder_text', db_session=session),
                        )
                        logger.info(f"{'reminder sended to ' + str(user)}")
                        await update_last_reminded_at(user_id=user.id, timestamp=datetime.now(timezone.utc), db_session=session)
                        await session.commit()


async def check_user_subscription(bot: Bot, db_connector: DatabaseConnector):
    utcnow = datetime.now(timezone.utc)
    current_hour = utcnow.hour
    if current_hour >= UTC_STARTING_MARK:
        hours_to_sleep = 24 - current_hour + UTC_STARTING_MARK
    else:
        hours_to_sleep = UTC_STARTING_MARK - current_hour
    seconds_to_sleep = hours_to_sleep * 3600 - utcnow.minute * 60 - utcnow.second
    await asyncio.sleep(seconds_to_sleep)
    while True:
        async with db_connector.session_factory() as session:
            for user in await get_all_users_with_active_subscription(session):
                utcnow = datetime.now(timezone.utc)
                delta = utcnow.date() - user.subscription_expired_at
                if delta.days == 1:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=await get_text_by_prompt(prompt='subscribtion_almost_over', db_session=session),
                        reply_markup=get_premium_keyboard(),
                    )
                    logger.info(f"{'ending subscription reminder was sent to ' + str(user)}")

                elif delta.days == 0:
                    user.subscription_status = UserSubscriptionType.ACCESS_EXPIRED
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=await get_text_by_prompt(prompt='subscribtion_over', db_session=session),
                        reply_markup=get_premium_keyboard(),
                    )
                    logger.info(f"{'ending subscription notification was sent to ' + str(user)}")
                    await session.commit()
        await asyncio.sleep(ONE_DAY)
