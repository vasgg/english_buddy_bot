from datetime import datetime, timedelta, timezone

from database.models.notification import NotificationCampaign, NotificationSegment
from database.models.user import User
from enums import (
    NotificationCampaignMode,
    NotificationTimeUnit,
    NotificationTimerAnchor,
    UserSubscriptionType,
)
from notifications.engine import (
    campaign_timer_delay,
    user_matches_exclusion_segment,
    user_passes_campaign_min_interval,
)


def _make_user() -> User:
    now = datetime.now(timezone.utc)
    user = User(
        telegram_id=1,
        fullname="Test User",
        username="test",
        last_reminded_at=now,
    )
    user.created_at = now - timedelta(days=10)
    user.last_activity_at = now - timedelta(days=5)
    user.last_lesson_completed_at = now - timedelta(days=3)
    user.last_notification_sent_at = now - timedelta(days=2)
    user.completed_all_lessons = False
    user.subscription_status = UserSubscriptionType.NO_ACCESS
    user.reminder_freq = None
    return user


def test_user_matches_exclusion_segment_without_conditions_is_false():
    user = _make_user()
    segment = NotificationSegment(campaign_id=1)
    now = datetime.now(timezone.utc)
    assert user_matches_exclusion_segment(user, segment, now=now) is False


def test_user_matches_exclusion_segment_with_multiple_conditions_and_logic():
    user = _make_user()
    segment = NotificationSegment(
        campaign_id=1,
        registration_age_from_hours=24,
        registration_age_to_hours=24 * 14,
        inactivity_from_hours=24,
        inactivity_to_hours=24 * 7,
        reminders_enabled=False,
        has_paid_subscription=False,
        completed_all_lessons=False,
    )
    now = datetime.now(timezone.utc)
    assert user_matches_exclusion_segment(user, segment, now=now) is True


def test_user_matches_exclusion_segment_excludes_when_required_timestamp_missing():
    user = _make_user()
    user.last_activity_at = None
    segment = NotificationSegment(
        campaign_id=1,
        inactivity_from_hours=24,
        inactivity_to_hours=24 * 7,
    )
    now = datetime.now(timezone.utc)
    assert user_matches_exclusion_segment(user, segment, now=now) is True


def test_user_passes_campaign_min_interval():
    user = _make_user()
    campaign = NotificationCampaign(
        name="Campaign",
        message_text="text",
        mode=NotificationCampaignMode.FILTER,
        min_interval_value=1,
        min_interval_unit=NotificationTimeUnit.DAYS,
    )
    now = datetime.now(timezone.utc)
    assert user_passes_campaign_min_interval(user, campaign, now=now) is True

    user.last_notification_sent_at = now - timedelta(hours=10)
    assert user_passes_campaign_min_interval(user, campaign, now=now) is False


def test_campaign_timer_delay_for_timer_mode():
    campaign = NotificationCampaign(
        name="Timer campaign",
        message_text="text",
        mode=NotificationCampaignMode.TIMER,
        timer_anchor=NotificationTimerAnchor.REGISTRATION,
        timer_value=5,
        timer_unit=NotificationTimeUnit.DAYS,
    )
    assert campaign_timer_delay(campaign) == timedelta(days=5)
