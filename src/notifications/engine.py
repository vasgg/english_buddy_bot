from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database.models.notification import NotificationCampaign, NotificationSegment
from database.models.user import User
from enums import NotificationCampaignMode, NotificationTimeUnit, NotificationTimerAnchor, UserSubscriptionType


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def unit_to_timedelta(value: int | None, unit: NotificationTimeUnit | None) -> timedelta | None:
    if value is None or value <= 0 or unit is None:
        return None
    if unit == NotificationTimeUnit.DAYS:
        return timedelta(days=value)
    return timedelta(hours=value)


def campaign_min_interval(campaign: NotificationCampaign) -> timedelta | None:
    return unit_to_timedelta(campaign.min_interval_value, campaign.min_interval_unit)


def campaign_timer_delay(campaign: NotificationCampaign) -> timedelta | None:
    if campaign.mode != NotificationCampaignMode.TIMER:
        return None
    return unit_to_timedelta(campaign.timer_value, campaign.timer_unit)


def timer_anchor_dt(user: User, campaign: NotificationCampaign) -> datetime | None:
    if campaign.timer_anchor == NotificationTimerAnchor.REGISTRATION:
        return ensure_utc(user.created_at)
    if campaign.timer_anchor == NotificationTimerAnchor.LAST_ACTIVITY:
        return ensure_utc(user.last_activity_at)
    if campaign.timer_anchor == NotificationTimerAnchor.LAST_LESSON_COMPLETED:
        return ensure_utc(user.last_lesson_completed_at)
    return None


def age_matches(
    timestamp: datetime | None, *, now: datetime, from_hours: int | None, to_hours: int | None
) -> bool | None:
    if from_hours is None and to_hours is None:
        return None
    if timestamp is None:
        return False
    ts = ensure_utc(timestamp)
    assert ts is not None
    age_hours = max(0.0, (now - ts).total_seconds() / 3600.0)
    if from_hours is not None and age_hours < from_hours:
        return False
    if to_hours is not None and age_hours > to_hours:
        return False
    return True


def user_has_paid_subscription(user: User) -> bool:
    return user.subscription_status in (
        UserSubscriptionType.LIMITED_ACCESS,
        UserSubscriptionType.UNLIMITED_ACCESS,
    )


def user_matches_exclusion_segment(user: User, segment: NotificationSegment | None, *, now: datetime) -> bool:
    if segment is None:
        return False

    # Fail-closed behavior: if a condition is configured but required timestamp is missing,
    # user is excluded from campaign delivery.
    if (
        segment.inactivity_from_hours is not None or segment.inactivity_to_hours is not None
    ) and user.last_activity_at is None:
        return True
    if (
        segment.lesson_completion_age_from_hours is not None or segment.lesson_completion_age_to_hours is not None
    ) and user.last_lesson_completed_at is None:
        return True
    if (
        segment.last_notification_age_from_hours is not None or segment.last_notification_age_to_hours is not None
    ) and user.last_notification_sent_at is None:
        return True

    checks: list[bool] = []

    registration_match = age_matches(
        user.created_at,
        now=now,
        from_hours=segment.registration_age_from_hours,
        to_hours=segment.registration_age_to_hours,
    )
    if registration_match is not None:
        checks.append(registration_match)

    inactivity_match = age_matches(
        user.last_activity_at,
        now=now,
        from_hours=segment.inactivity_from_hours,
        to_hours=segment.inactivity_to_hours,
    )
    if inactivity_match is not None:
        checks.append(inactivity_match)

    lesson_completion_match = age_matches(
        user.last_lesson_completed_at,
        now=now,
        from_hours=segment.lesson_completion_age_from_hours,
        to_hours=segment.lesson_completion_age_to_hours,
    )
    if lesson_completion_match is not None:
        checks.append(lesson_completion_match)

    last_notification_match = age_matches(
        user.last_notification_sent_at,
        now=now,
        from_hours=segment.last_notification_age_from_hours,
        to_hours=segment.last_notification_age_to_hours,
    )
    if last_notification_match is not None:
        checks.append(last_notification_match)

    if segment.reminders_enabled is not None:
        checks.append((user.reminder_freq is not None) == segment.reminders_enabled)

    if segment.has_paid_subscription is not None:
        checks.append(user_has_paid_subscription(user) == segment.has_paid_subscription)

    if segment.completed_all_lessons is not None:
        checks.append(user.completed_all_lessons == segment.completed_all_lessons)

    return bool(checks) and all(checks)


def user_passes_campaign_min_interval(user: User, campaign: NotificationCampaign, *, now: datetime) -> bool:
    min_interval = campaign_min_interval(campaign)
    if min_interval is None:
        return True
    last_notification_at = ensure_utc(user.last_notification_sent_at)
    if last_notification_at is None:
        return True
    return now - last_notification_at >= min_interval
