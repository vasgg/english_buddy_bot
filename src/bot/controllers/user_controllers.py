import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, types
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.keyboards import get_lesson_picker_keyboard, get_notified_keyboard, get_premium_keyboard
from bot.internal.notify_admin import notify_admin_about_exception
from config import get_settings
from consts import ONE_DAY, ONE_HOUR, UTC_STARTING_MARK
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import get_active_and_editing_lessons, get_active_lessons, get_completed_lessons_from_sessions
from database.crud.user import (
    get_all_users_with_active_subscription,
    get_all_users_with_reminders,
    update_last_reminded_at,
)
from database.database_connector import DatabaseConnector
from database.garbage_helper import collect_garbage
from enums import UserSubscriptionType

logger = logging.getLogger()


def get_seconds_until_starting_mark(current_hour, utcnow):
    if current_hour >= UTC_STARTING_MARK:
        hours_to_sleep = 24 - current_hour + UTC_STARTING_MARK
    else:
        hours_to_sleep = UTC_STARTING_MARK - current_hour
    seconds_to_sleep = hours_to_sleep * 3600 - utcnow.minute * 60 - utcnow.second
    return seconds_to_sleep


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def _mark_failed_delivery(user, *, reason: str) -> None:
    logger.warning("Telegram refused delivery to %s: %s", user, reason)


async def propose_reminder_to_user(message: types.Message, db_session: AsyncSession) -> None:
    await message.answer(
        text=await get_text_by_prompt(prompt='registration_message', db_session=db_session),
        reply_markup=get_notified_keyboard(),
    )


async def show_start_menu(event: types.Message, user_id: int, db_session: AsyncSession) -> None:
    if event.from_user.id not in get_settings().TEACHERS:
        lessons = await get_active_lessons(db_session)
    else:
        lessons = await get_active_and_editing_lessons(db_session)
    completed_lessons = await get_completed_lessons_from_sessions(user_id=user_id, db_session=db_session)
    await event.answer(
        text=await get_text_by_prompt(prompt='start_message', db_session=db_session),
        reply_markup=get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )


async def check_user_reminders(bot: Bot, db_connector: DatabaseConnector):
    while True:
        await asyncio.sleep(ONE_HOUR)
        try:
            utcnow = datetime.now(timezone.utc)
            if utcnow.hour == UTC_STARTING_MARK - 1:
                wait_seconds = ONE_HOUR - utcnow.minute * 60 - utcnow.second
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                async with db_connector.session_factory() as session:
                    reminder_text = await get_text_by_prompt(prompt='reminder_text', db_session=session)
                    for user in await get_all_users_with_reminders(session):
                        last_reminded_at = ensure_utc(user.last_reminded_at)
                        reminder_due = datetime.now(timezone.utc)
                        if reminder_due - last_reminded_at > timedelta(days=user.reminder_freq):
                            try:
                                await bot.send_message(chat_id=user.telegram_id, text=reminder_text)
                            except (TelegramForbiddenError, TelegramNotFound) as exc:
                                await _mark_failed_delivery(user, reason=f"Telegram delivery error: {exc}")
                                await update_last_reminded_at(
                                    user_id=user.id, timestamp=reminder_due, db_session=session
                                )
                            except Exception as send_exc:  # noqa: BLE001
                                logger.exception("Failed to send reminder to %s", user, exc_info=send_exc)
                            else:
                                logger.info("Reminder sent to %s", user)
                                await update_last_reminded_at(
                                    user_id=user.id, timestamp=reminder_due, db_session=session
                                )
                    await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Failed to process reminder check", exc_info=exc)
            await notify_admin_about_exception(bot, exc, context="check_user_reminders")


async def daily_routine(bot: Bot, db_connector: DatabaseConnector):
    utcnow = datetime.now(timezone.utc)
    current_hour = utcnow.hour
    seconds_to_sleep = get_seconds_until_starting_mark(current_hour, utcnow)
    if seconds_to_sleep > 0:
        await asyncio.sleep(seconds_to_sleep)
    while True:
        try:
            async with db_connector.session_factory() as session:
                await collect_garbage(session)
                users = await get_all_users_with_active_subscription(session)
                today_utc = datetime.now(timezone.utc).date()
                for user in users:
                    if not user.subscription_expired_at:
                        continue
                    delta_days = (today_utc - user.subscription_expired_at).days
                    if delta_days == 1:
                        try:
                            await bot.send_message(
                                chat_id=user.telegram_id,
                                text=await get_text_by_prompt(prompt='subscribtion_almost_over', db_session=session),
                                reply_markup=get_premium_keyboard(),
                            )
                        except (TelegramForbiddenError, TelegramNotFound) as exc:
                            await _mark_failed_delivery(user, reason=f"Telegram delivery error: {exc}")
                        except Exception as send_exc:  # noqa: BLE001
                            logger.exception("Failed to send subscription reminder to %s", user, exc_info=send_exc)
                        else:
                            logger.info("Ending subscription reminder was sent to %s", user)

                    elif delta_days == 0:
                        user.subscription_status = UserSubscriptionType.ACCESS_EXPIRED
                        try:
                            await bot.send_message(
                                chat_id=user.telegram_id,
                                text=await get_text_by_prompt(prompt='subscribtion_over', db_session=session),
                                reply_markup=get_premium_keyboard(),
                            )
                        except (TelegramForbiddenError, TelegramNotFound) as exc:
                            await _mark_failed_delivery(user, reason=f"Telegram delivery error: {exc}")
                        except Exception as send_exc:  # noqa: BLE001
                            logger.exception("Failed to send subscription expiration notice to %s", user, exc_info=send_exc)
                        else:
                            logger.info("Ending subscription notification was sent to %s", user)
                await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Failed to process daily routine", exc_info=exc)
            await notify_admin_about_exception(bot, exc, context="daily_routine")
        await asyncio.sleep(ONE_DAY)
