import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from aiogram import Bot, types
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.keyboards import get_lesson_picker_keyboard, get_notified_keyboard, get_premium_keyboard
from bot.internal.notify_admin import notify_admin_about_exception
from config import get_settings
from consts import ONE_DAY, UTC_STARTING_MARK
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import (
    get_active_and_editing_lessons,
    get_active_lessons,
    get_completed_lessons_from_sessions,
)
from database.crud.reminder_text_variant import get_all_reminder_text_variants
from database.crud.user import (
    get_all_users_with_active_subscription,
    get_all_users_with_reminders,
    set_subscription_status,
    update_last_reminded_at,
)
from database.database_connector import DatabaseConnector
from database.garbage_helper import collect_garbage
from enums import UserSubscriptionType

logger = logging.getLogger()


def _normalize_reminder_variants(variants: list[str]) -> list[str]:
    unique_variants = dict.fromkeys(variants)
    return [text for text in unique_variants if text and text.strip()]


@dataclass
class _NonRepeatingTextPicker:
    source_key: tuple[str, ...] | None = None
    pool: list[str] = field(default_factory=list)

    def pick(self, variants: list[str]) -> str:
        key = tuple(variants)
        if self.source_key != key:
            self.source_key = key
            self.pool.clear()

        if not self.pool:
            self.pool.extend(variants)

        choice = random.choice(self.pool)
        self.pool.remove(choice)
        return choice


_reminder_text_picker = _NonRepeatingTextPicker()


def _pick_reminder_text(reminder_text_variants: list[str], reminder_text_fallback: str | None) -> str | None:
    normalized = _normalize_reminder_variants(reminder_text_variants)
    if normalized:
        return _reminder_text_picker.pick(normalized)
    return reminder_text_fallback


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


def get_reminder_slot(utcnow: datetime) -> datetime:
    if utcnow.tzinfo is None:
        utcnow = utcnow.replace(tzinfo=timezone.utc)
    slot = utcnow.replace(hour=UTC_STARTING_MARK, minute=0, second=0, microsecond=0)
    if utcnow < slot:
        slot -= timedelta(days=1)
    return slot


async def _mark_failed_delivery(user, *, reason: str) -> None:
    logger.warning("Telegram refused delivery to %s: %s", user, reason)


async def _update_reminder_timestamp(
    db_connector: DatabaseConnector,
    *,
    user_id: int,
    timestamp: datetime,
) -> None:
    async with db_connector.session_factory.begin() as session:
        await update_last_reminded_at(user_id=user_id, timestamp=timestamp, db_session=session)


async def _set_subscription_status(
    db_connector: DatabaseConnector,
    *,
    user_id: int,
    new_status: UserSubscriptionType,
) -> None:
    async with db_connector.session_factory.begin() as session:
        await set_subscription_status(user_id=user_id, new_status=new_status, db_session=session)


async def propose_reminder_to_user(message: types.Message, db_session: AsyncSession) -> None:
    await message.answer(
        text=await get_text_by_prompt(prompt="registration_message", db_session=db_session),
        reply_markup=get_notified_keyboard(),
    )


async def show_start_menu(event: types.Message, user_id: int, db_session: AsyncSession) -> None:
    if event.from_user.id not in get_settings().TEACHERS:
        lessons = await get_active_lessons(db_session)
    else:
        lessons = await get_active_and_editing_lessons(db_session)
    completed_lessons = await get_completed_lessons_from_sessions(user_id=user_id, db_session=db_session)
    await event.answer(
        text=await get_text_by_prompt(prompt="start_message", db_session=db_session),
        reply_markup=get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )


async def check_user_reminders(bot: Bot, db_connector: DatabaseConnector):
    while True:
        try:
            utcnow = datetime.now(timezone.utc)
            wait_seconds = get_seconds_until_starting_mark(utcnow.hour, utcnow)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            reminder_due = get_reminder_slot(datetime.now(timezone.utc))
            async with db_connector.session_factory() as session:
                try:
                    reminder_text_variants = await get_all_reminder_text_variants(session)
                except OperationalError:
                    reminder_text_variants = []
                reminder_text_fallback = None
                if not reminder_text_variants:
                    reminder_text_fallback = await get_text_by_prompt(prompt="reminder_text", db_session=session)
                reminder_recipients = [
                    {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "last_reminded_at": get_reminder_slot(ensure_utc(user.last_reminded_at)),
                        "reminder_freq": user.reminder_freq,
                        "log_repr": str(user),
                    }
                    for user in await get_all_users_with_reminders(session)
                ]
            for recipient in reminder_recipients:
                user_id = recipient["id"]
                telegram_id = recipient["telegram_id"]
                last_reminded_at = recipient["last_reminded_at"]
                reminder_freq = recipient["reminder_freq"]
                log_repr = recipient["log_repr"]
                if reminder_freq is None:
                    continue
                if reminder_due - last_reminded_at < timedelta(days=reminder_freq):
                    continue
                try:
                    reminder_text = _pick_reminder_text(reminder_text_variants, reminder_text_fallback)
                    if reminder_text is None:
                        continue
                    await bot.send_message(chat_id=telegram_id, text=reminder_text)
                except (TelegramForbiddenError, TelegramNotFound) as exc:
                    await _mark_failed_delivery(log_repr, reason=f"Telegram delivery error: {exc}")
                    await _update_reminder_timestamp(
                        db_connector,
                        user_id=user_id,
                        timestamp=reminder_due,
                    )
                except Exception as send_exc:  # noqa: BLE001
                    logger.exception("Failed to send reminder to %s", log_repr, exc_info=send_exc)
                else:
                    logger.info("Reminder sent to %s", log_repr)
                    await _update_reminder_timestamp(
                        db_connector,
                        user_id=user_id,
                        timestamp=reminder_due,
                    )
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
            async with db_connector.session_factory.begin() as session:
                await collect_garbage(session)

            async with db_connector.session_factory() as session:
                almost_over_text = await get_text_by_prompt(prompt="subscribtion_almost_over", db_session=session)
                over_text = await get_text_by_prompt(prompt="subscribtion_over", db_session=session)
                users = [
                    {
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "subscription_expired_at": user.subscription_expired_at,
                        "log_repr": str(user),
                    }
                    for user in await get_all_users_with_active_subscription(session)
                ]

            today_utc = datetime.now(timezone.utc).date()
            for user in users:
                if not user["subscription_expired_at"]:
                    continue
                days_to_expiry = (user["subscription_expired_at"] - today_utc).days
                if days_to_expiry == 1:
                    try:
                        await bot.send_message(
                            chat_id=user["telegram_id"],
                            text=almost_over_text,
                            reply_markup=get_premium_keyboard(),
                        )
                    except (TelegramForbiddenError, TelegramNotFound) as exc:
                        await _mark_failed_delivery(user["log_repr"], reason=f"Telegram delivery error: {exc}")
                    except Exception as send_exc:  # noqa: BLE001
                        logger.exception(
                            "Failed to send subscription reminder to %s", user["log_repr"], exc_info=send_exc
                        )
                    else:
                        logger.info("Ending subscription reminder was sent to %s", user["log_repr"])

                elif days_to_expiry == 0:
                    await _set_subscription_status(
                        db_connector,
                        user_id=user["id"],
                        new_status=UserSubscriptionType.ACCESS_EXPIRED,
                    )
                    try:
                        await bot.send_message(
                            chat_id=user["telegram_id"],
                            text=over_text,
                            reply_markup=get_premium_keyboard(),
                        )
                    except (TelegramForbiddenError, TelegramNotFound) as exc:
                        await _mark_failed_delivery(user["log_repr"], reason=f"Telegram delivery error: {exc}")
                    except Exception as send_exc:  # noqa: BLE001
                        logger.exception(
                            "Failed to send subscription expiration notice to %s",
                            user["log_repr"],
                            exc_info=send_exc,
                        )
                    else:
                        logger.info("Ending subscription notification was sent to %s", user["log_repr"])
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Failed to process daily routine", exc_info=exc)
            await notify_admin_about_exception(bot, exc, context="daily_routine")
        await asyncio.sleep(ONE_DAY)
