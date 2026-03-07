import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound
from aiogram.types import FSInputFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bot.controllers.user_controllers import _pick_reminder_text, ensure_utc, get_reminder_slot
from bot.internal.notify_admin import notify_admin_about_exception
from bot.keyboards.keyboards import get_premium_keyboard
from config import get_settings
from consts import UTC_STARTING_MARK
from database.crud.answer import get_text_by_prompt
from database.crud.reminder_text_variant import get_all_reminder_text_variants
from database.crud.user import (
    get_all_users_with_active_subscription,
    get_all_users_with_reminders,
    set_user_bot_blocked,
    set_subscription_status,
    update_last_notification_sent_at,
    update_last_reminded_at,
)
from database.garbage_helper import collect_garbage
from database.models.notification import NotificationCampaign, NotificationDelivery, NotificationSegment
from database.models.user import User
from database.tables_helper import get_db
from enums import (
    NotificationCampaignMode,
    NotificationCampaignStatus,
    NotificationDeliveryStatus,
    UserSubscriptionType,
)
from notifications.engine import (
    campaign_timer_delay,
    ensure_utc as ensure_utc_notification,
    timer_anchor_dt,
    user_matches_exclusion_segment,
    user_passes_campaign_min_interval,
)
from notifications.delivery import send_with_single_retry, should_send_image_separately
from tasks.broker import broker

logger = logging.getLogger(__name__)
db = get_db()

CAMPAIGN_PROCESS_CRON = "*/15 * * * *"
TELEGRAM_THROTTLE_SECONDS = 0.5


async def _update_reminder_timestamp(user_id: int, timestamp: datetime, *, bot_blocked: bool | None = None) -> None:
    async with db.session_factory.begin() as session:
        await update_last_reminded_at(user_id=user_id, timestamp=timestamp, db_session=session)
        await update_last_notification_sent_at(user_id=user_id, timestamp=timestamp, db_session=session)
        if bot_blocked is not None:
            await set_user_bot_blocked(user_id=user_id, bot_blocked=bot_blocked, db_session=session)


async def _mark_notification_timestamp(
    user_id: int,
    timestamp: datetime,
    *,
    bot_blocked: bool | None = None,
) -> None:
    async with db.session_factory.begin() as session:
        await update_last_notification_sent_at(user_id=user_id, timestamp=timestamp, db_session=session)
        if bot_blocked is not None:
            await set_user_bot_blocked(user_id=user_id, bot_blocked=bot_blocked, db_session=session)


async def _set_user_bot_blocked(user_id: int, bot_blocked: bool) -> None:
    async with db.session_factory.begin() as session:
        await set_user_bot_blocked(user_id=user_id, bot_blocked=bot_blocked, db_session=session)


async def _set_subscription_status(user_id: int, new_status: UserSubscriptionType) -> None:
    async with db.session_factory.begin() as session:
        await set_subscription_status(user_id=user_id, new_status=new_status, db_session=session)


def _cron_at_starting_mark() -> str:
    # Run every day at `UTC_STARTING_MARK:00` UTC.
    return f"0 {UTC_STARTING_MARK} * * *"


def _filter_due_for_processing(campaign: NotificationCampaign, now: datetime) -> bool:
    check_every_hours = campaign.check_every_hours or 24
    if check_every_hours < 1:
        check_every_hours = 1
    if campaign.last_processed_at is None:
        return True
    return now - ensure_utc_notification(campaign.last_processed_at) >= timedelta(hours=check_every_hours)


async def _touch_campaign_processed_at(campaign_id: int, timestamp: datetime) -> None:
    async with db.session_factory.begin() as session:
        campaign = await session.get(NotificationCampaign, campaign_id)
        if campaign is None:
            return
        campaign.last_processed_at = timestamp


async def _get_campaign_payload(
    campaign_id: int,
) -> tuple[NotificationCampaign, NotificationSegment | None, list[User], set[int]] | None:
    async with db.session_factory() as session:
        campaign = await session.get(NotificationCampaign, campaign_id)
        if campaign is None:
            return None
        segment_query = select(NotificationSegment).filter(NotificationSegment.campaign_id == campaign.id)
        segment = (await session.execute(segment_query)).scalars().first()

        users_query = select(User)
        users = list((await session.execute(users_query)).scalars().all())

        delivered_users_query = select(NotificationDelivery.user_id).filter(
            NotificationDelivery.campaign_id == campaign.id
        )
        processed_user_ids = set((await session.execute(delivered_users_query)).scalars().all())

        return campaign, segment, users, processed_user_ids


async def _reserve_delivery(campaign_id: int, user_id: int, scheduled_at: datetime) -> int | None:
    try:
        async with db.session_factory.begin() as session:
            existing_query = select(NotificationDelivery.id).filter(
                NotificationDelivery.campaign_id == campaign_id,
                NotificationDelivery.user_id == user_id,
            )
            existing_delivery_id = (await session.execute(existing_query)).scalar_one_or_none()
            if existing_delivery_id is not None:
                return None

            delivery = NotificationDelivery(
                campaign_id=campaign_id,
                user_id=user_id,
                scheduled_at=scheduled_at,
                status=NotificationDeliveryStatus.QUEUED,
                attempts=0,
            )
            session.add(delivery)
            await session.flush()
            return delivery.id
    except IntegrityError:
        # Another worker reserved this delivery concurrently.
        return None


async def _complete_delivery(
    *,
    delivery_id: int,
    user_id: int,
    status: NotificationDeliveryStatus,
    attempts: int,
    sent_at: datetime | None,
    last_error: str | None,
    mark_last_notification_timestamp: bool,
    bot_blocked: bool | None,
) -> None:
    async with db.session_factory.begin() as session:
        delivery = await session.get(NotificationDelivery, delivery_id)
        if delivery is None:
            return
        delivery.status = status
        delivery.attempts = attempts
        delivery.last_error = last_error
        delivery.sent_at = sent_at

        if mark_last_notification_timestamp and sent_at is not None:
            await update_last_notification_sent_at(user_id=user_id, timestamp=sent_at, db_session=session)
        if bot_blocked is not None:
            await set_user_bot_blocked(user_id=user_id, bot_blocked=bot_blocked, db_session=session)


async def _create_skipped_delivery_if_absent(
    *,
    campaign_id: int,
    user_id: int,
    scheduled_at: datetime,
    reason: str,
) -> None:
    delivery_id = await _reserve_delivery(campaign_id=campaign_id, user_id=user_id, scheduled_at=scheduled_at)
    if delivery_id is None:
        return
    await _complete_delivery(
        delivery_id=delivery_id,
        user_id=user_id,
        status=NotificationDeliveryStatus.SKIPPED,
        attempts=0,
        sent_at=None,
        last_error=reason,
        mark_last_notification_timestamp=False,
        bot_blocked=None,
    )


async def _send_campaign_message(bot: Bot, campaign: NotificationCampaign, user: User) -> None:
    disable_notification = bool(campaign.is_silent)

    if campaign.image_path:
        image_path = Path(campaign.image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {campaign.image_path}")

        if should_send_image_separately(
            campaign.message_text,
            send_image_separately=bool(campaign.send_image_separately),
        ):
            await bot.send_photo(
                chat_id=user.telegram_id,
                photo=FSInputFile(image_path),
                disable_notification=disable_notification,
            )
            await bot.send_message(
                chat_id=user.telegram_id,
                text=campaign.message_text,
                disable_notification=disable_notification,
            )
            return

        await bot.send_photo(
            chat_id=user.telegram_id,
            photo=FSInputFile(image_path),
            caption=campaign.message_text,
            disable_notification=disable_notification,
            parse_mode=ParseMode.HTML,
        )
        return

    await bot.send_message(
        chat_id=user.telegram_id,
        text=campaign.message_text,
        disable_notification=disable_notification,
    )


async def _attempt_campaign_delivery(
    *,
    bot: Bot,
    campaign: NotificationCampaign,
    user: User,
    scheduled_at: datetime,
) -> None:
    delivery_id = await _reserve_delivery(campaign_id=campaign.id, user_id=user.id, scheduled_at=scheduled_at)
    if delivery_id is None:
        return

    attempts, send_error = await send_with_single_retry(
        lambda: _send_campaign_message(bot, campaign, user),
        logger=logger,
    )
    sent_at = datetime.now(timezone.utc)

    if send_error is None:
        logger.info("Campaign %s sent to %s", campaign.id, user)
        await _complete_delivery(
            delivery_id=delivery_id,
            user_id=user.id,
            status=NotificationDeliveryStatus.SENT,
            attempts=attempts,
            sent_at=sent_at,
            last_error=None,
            mark_last_notification_timestamp=True,
            bot_blocked=False,
        )
        return

    if isinstance(send_error, (TelegramForbiddenError, TelegramNotFound)):
        exc = send_error
        logger.warning("Telegram refused campaign delivery to %s for campaign %s: %s", user, campaign.id, exc)
        await _complete_delivery(
            delivery_id=delivery_id,
            user_id=user.id,
            status=NotificationDeliveryStatus.FAILED,
            attempts=attempts,
            sent_at=sent_at,
            last_error=str(exc),
            mark_last_notification_timestamp=True,
            bot_blocked=True,
        )
        return

    logger.exception("Failed campaign delivery to %s for campaign %s", user, campaign.id, exc_info=send_error)
    await _complete_delivery(
        delivery_id=delivery_id,
        user_id=user.id,
        status=NotificationDeliveryStatus.FAILED,
        attempts=attempts,
        sent_at=None,
        last_error=str(send_error),
        mark_last_notification_timestamp=False,
        bot_blocked=None,
    )


async def _process_filter_campaign(
    *,
    bot: Bot,
    campaign: NotificationCampaign,
    segment: NotificationSegment | None,
    users: list[User],
    processed_user_ids: set[int],
    now: datetime,
) -> None:
    if not _filter_due_for_processing(campaign, now):
        return

    for user in users:
        if user.id in processed_user_ids:
            continue
        if user_matches_exclusion_segment(user, segment, now=now):
            continue
        if not user_passes_campaign_min_interval(user, campaign, now=now):
            continue

        await _attempt_campaign_delivery(
            bot=bot,
            campaign=campaign,
            user=user,
            scheduled_at=now,
        )
        await asyncio.sleep(TELEGRAM_THROTTLE_SECONDS)

    await _touch_campaign_processed_at(campaign.id, now)


async def _process_timer_campaign(
    *,
    bot: Bot,
    campaign: NotificationCampaign,
    segment: NotificationSegment | None,
    users: list[User],
    processed_user_ids: set[int],
    now: datetime,
) -> None:
    delay = campaign_timer_delay(campaign)
    if delay is None or campaign.timer_anchor is None:
        logger.warning("Timer campaign %s is missing timer config", campaign.id)
        await _touch_campaign_processed_at(campaign.id, now)
        return

    activated_at = ensure_utc_notification(campaign.activated_at) or ensure_utc_notification(campaign.created_at)
    assert activated_at is not None

    for user in users:
        if user.id in processed_user_ids:
            continue

        anchor_dt = timer_anchor_dt(user, campaign)
        if anchor_dt is None:
            # No anchor yet, this user may become eligible later.
            continue

        due_at = anchor_dt + delay
        if due_at < activated_at:
            await _create_skipped_delivery_if_absent(
                campaign_id=campaign.id,
                user_id=user.id,
                scheduled_at=due_at,
                reason="Timer overdue at activation",
            )
            continue

        if due_at > now:
            continue

        if user_matches_exclusion_segment(user, segment, now=now):
            await _create_skipped_delivery_if_absent(
                campaign_id=campaign.id,
                user_id=user.id,
                scheduled_at=due_at,
                reason="Excluded by campaign conditions",
            )
            continue

        if not user_passes_campaign_min_interval(user, campaign, now=now):
            await _create_skipped_delivery_if_absent(
                campaign_id=campaign.id,
                user_id=user.id,
                scheduled_at=due_at,
                reason="Global min interval not reached",
            )
            continue

        await _attempt_campaign_delivery(
            bot=bot,
            campaign=campaign,
            user=user,
            scheduled_at=due_at,
        )
        await asyncio.sleep(TELEGRAM_THROTTLE_SECONDS)

    await _touch_campaign_processed_at(campaign.id, now)


async def _process_single_campaign(bot: Bot, campaign_id: int, now: datetime) -> None:
    payload = await _get_campaign_payload(campaign_id)
    if payload is None:
        return

    campaign, segment, users, processed_user_ids = payload
    if campaign.status != NotificationCampaignStatus.ACTIVE:
        return

    if campaign.mode == NotificationCampaignMode.FILTER:
        await _process_filter_campaign(
            bot=bot,
            campaign=campaign,
            segment=segment,
            users=users,
            processed_user_ids=processed_user_ids,
            now=now,
        )
        return

    await _process_timer_campaign(
        bot=bot,
        campaign=campaign,
        segment=segment,
        users=users,
        processed_user_ids=processed_user_ids,
        now=now,
    )


@broker.task(schedule=[{"cron": CAMPAIGN_PROCESS_CRON}])
async def process_notification_campaigns() -> None:
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        now = datetime.now(timezone.utc)
        async with db.session_factory() as session:
            campaigns_query = select(NotificationCampaign.id).filter(
                NotificationCampaign.status == NotificationCampaignStatus.ACTIVE
            )
            campaign_ids = list((await session.execute(campaigns_query)).scalars().all())

        for campaign_id in campaign_ids:
            try:
                await _process_single_campaign(bot=bot, campaign_id=campaign_id, now=now)
            except Exception as campaign_exc:  # noqa: BLE001
                logger.exception("Failed processing campaign %s", campaign_id, exc_info=campaign_exc)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to process notification campaigns", exc_info=exc)
        await notify_admin_about_exception(bot, exc, context="process_notification_campaigns")
        raise
    finally:
        await bot.session.close()


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
                await _update_reminder_timestamp(user_id=user.id, timestamp=reminder_due, bot_blocked=True)
            except Exception as send_exc:  # noqa: BLE001
                logger.exception("Failed to send reminder to %s", user, exc_info=send_exc)
            else:
                logger.info("Reminder sent to %s", user)
                await _update_reminder_timestamp(user_id=user.id, timestamp=reminder_due, bot_blocked=False)

            # Basic throttle to reduce risk of hitting Telegram limits.
            await asyncio.sleep(0.5)
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
                    await _set_user_bot_blocked(user_id=user.id, bot_blocked=True)
                except Exception as send_exc:  # noqa: BLE001
                    logger.exception("Failed to send subscription reminder to %s", user, exc_info=send_exc)
                else:
                    logger.info("Ending subscription reminder was sent to %s", user)
                    await _mark_notification_timestamp(
                        user_id=user.id,
                        timestamp=datetime.now(timezone.utc),
                        bot_blocked=False,
                    )
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
                    await _set_user_bot_blocked(user_id=user.id, bot_blocked=True)
                except Exception as send_exc:  # noqa: BLE001
                    logger.exception("Failed to send subscription expiration notice to %s", user, exc_info=send_exc)
                else:
                    logger.info("Ending subscription notification was sent to %s", user)
                    await _mark_notification_timestamp(
                        user_id=user.id,
                        timestamp=datetime.now(timezone.utc),
                        bot_blocked=False,
                    )

            await asyncio.sleep(0.5)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to process daily routine", exc_info=exc)
        await notify_admin_about_exception(bot, exc, context="process_daily_routine")
        raise
    finally:
        await bot.session.close()
