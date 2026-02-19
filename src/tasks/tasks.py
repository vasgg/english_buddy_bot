import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound

from bot.keyboards.keyboards import get_premium_keyboard
from bot.internal.notify_admin import notify_admin_about_exception
from bot.controllers.user_controllers import ensure_utc, get_reminder_slot, _pick_reminder_text
from config import get_settings
from consts import UTC_STARTING_MARK
from database.crud.answer import get_text_by_prompt
from database.crud.reminder_text_variant import get_all_reminder_text_variants
from database.crud.user import (
    get_all_users_with_active_subscription,
    get_all_users_with_reminders,
    set_subscription_status,
    update_last_reminded_at,
)
from database.garbage_helper import collect_garbage
from database.tables_helper import get_db
from enums import UserSubscriptionType
from tasks.broker import broker

logger = logging.getLogger(__name__)
db = get_db()


async def _update_reminder_timestamp(user_id: int, timestamp: datetime) -> None:
    async with db.session_factory.begin() as session:
        await update_last_reminded_at(user_id=user_id, timestamp=timestamp, db_session=session)


async def _set_subscription_status(user_id: int, new_status: UserSubscriptionType) -> None:
    async with db.session_factory.begin() as session:
        await set_subscription_status(user_id=user_id, new_status=new_status, db_session=session)


def _cron_at_starting_mark() -> str:
    # Run every day at `UTC_STARTING_MARK:00` UTC.
    return f"0 {UTC_STARTING_MARK} * * *"


@broker.task(schedule=[{"cron": _cron_at_starting_mark()}])
async def process_user_reminders() -> None:
    """
    Replacement for the old `check_user_reminders()` loop.
    This task is expected to be triggered by Taskiq scheduler once per day.
    """
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        utcnow = datetime.now(timezone.utc)
        reminder_due = get_reminder_slot(utcnow)

        async with db.session_factory() as session:
            reminder_text_variants = await get_all_reminder_text_variants(session)
            reminder_text_fallback = None
            if not reminder_text_variants:
                reminder_text_fallback = await get_text_by_prompt(prompt="reminder_text", db_session=session)
            users = await get_all_users_with_reminders(session)

        for user in users:
            if user.reminder_freq is None:
                continue
            last_reminded_at = get_reminder_slot(ensure_utc(user.last_reminded_at))
            if reminder_due - last_reminded_at < timedelta(days=user.reminder_freq):
                continue

            reminder_text = _pick_reminder_text(reminder_text_variants, reminder_text_fallback)
            if reminder_text is None:
                continue

            try:
                await bot.send_message(chat_id=user.telegram_id, text=reminder_text)
            except (TelegramForbiddenError, TelegramNotFound) as exc:
                logger.warning("Telegram refused delivery to %s: %s", user, exc)
                await _update_reminder_timestamp(user_id=user.id, timestamp=reminder_due)
            except Exception as send_exc:  # noqa: BLE001
                logger.exception("Failed to send reminder to %s", user, exc_info=send_exc)
            else:
                logger.info("Reminder sent to %s", user)
                await _update_reminder_timestamp(user_id=user.id, timestamp=reminder_due)

            # Basic throttle to reduce risk of hitting Telegram limits.
            await asyncio.sleep(0.05)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to process reminders", exc_info=exc)
        await notify_admin_about_exception(bot, exc, context="process_user_reminders")
        raise
    finally:
        await bot.session.close()


@broker.task(schedule=[{"cron": _cron_at_starting_mark()}])
async def process_daily_routine() -> None:
    """
    Replacement for the old `daily_routine()` loop.
    """
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        async with db.session_factory.begin() as session:
            await collect_garbage(session)

        async with db.session_factory() as session:
            almost_over_text = await get_text_by_prompt(prompt="subscribtion_almost_over", db_session=session)
            over_text = await get_text_by_prompt(prompt="subscribtion_over", db_session=session)
            users = await get_all_users_with_active_subscription(session)

        today_utc = datetime.now(timezone.utc).date()
        for user in users:
            if not user.subscription_expired_at:
                continue
            days_to_expiry = (user.subscription_expired_at - today_utc).days
            if days_to_expiry == 1:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=almost_over_text,
                        reply_markup=get_premium_keyboard(),
                    )
                except (TelegramForbiddenError, TelegramNotFound) as exc:
                    logger.warning("Telegram refused delivery to %s: %s", user, exc)
                except Exception as send_exc:  # noqa: BLE001
                    logger.exception("Failed to send subscription reminder to %s", user, exc_info=send_exc)
                else:
                    logger.info("Ending subscription reminder was sent to %s", user)
            elif days_to_expiry == 0:
                await _set_subscription_status(user_id=user.id, new_status=UserSubscriptionType.ACCESS_EXPIRED)
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=over_text,
                        reply_markup=get_premium_keyboard(),
                    )
                except (TelegramForbiddenError, TelegramNotFound) as exc:
                    logger.warning("Telegram refused delivery to %s: %s", user, exc)
                except Exception as send_exc:  # noqa: BLE001
                    logger.exception("Failed to send subscription expiration notice to %s", user, exc_info=send_exc)
                else:
                    logger.info("Ending subscription notification was sent to %s", user)

            await asyncio.sleep(0.05)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to process daily routine", exc_info=exc)
        await notify_admin_about_exception(bot, exc, context="process_daily_routine")
        raise
    finally:
        await bot.session.close()
