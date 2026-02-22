from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import (
    NotificationCampaignMode,
    NotificationCampaignStatus,
    NotificationDeliveryStatus,
    NotificationSegmentMode,
    NotificationTimeUnit,
    NotificationTimerAnchor,
)


class NotificationCampaign(Base):
    __tablename__ = "notification_campaigns"

    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[NotificationCampaignStatus] = mapped_column(
        default=NotificationCampaignStatus.DRAFT,
        server_default=NotificationCampaignStatus.DRAFT.name,
    )
    message_text: Mapped[str] = mapped_column(Text)
    mode: Mapped[NotificationCampaignMode] = mapped_column(
        default=NotificationCampaignMode.FILTER,
        server_default=NotificationCampaignMode.FILTER.name,
    )
    check_every_hours: Mapped[int | None] = mapped_column(Integer)
    timer_anchor: Mapped[NotificationTimerAnchor | None] = mapped_column()
    timer_value: Mapped[int | None] = mapped_column(Integer)
    timer_unit: Mapped[NotificationTimeUnit | None] = mapped_column()
    min_interval_value: Mapped[int | None] = mapped_column(Integer)
    min_interval_unit: Mapped[NotificationTimeUnit | None] = mapped_column()
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    image_path: Mapped[str | None] = mapped_column(String(512))
    send_image_separately: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str | None] = mapped_column(String(64))
    is_silent: Mapped[bool | None] = mapped_column(Boolean)


class NotificationSegment(Base):
    __tablename__ = "notification_segments"

    campaign_id: Mapped[int] = mapped_column(ForeignKey("notification_campaigns.id", ondelete="CASCADE"))
    mode: Mapped[NotificationSegmentMode] = mapped_column(
        default=NotificationSegmentMode.EXCLUDE,
        server_default=NotificationSegmentMode.EXCLUDE.name,
    )
    name: Mapped[str | None] = mapped_column(String(128))
    registration_age_from_hours: Mapped[int | None] = mapped_column(Integer)
    registration_age_to_hours: Mapped[int | None] = mapped_column(Integer)
    inactivity_from_hours: Mapped[int | None] = mapped_column(Integer)
    inactivity_to_hours: Mapped[int | None] = mapped_column(Integer)
    lesson_completion_age_from_hours: Mapped[int | None] = mapped_column(Integer)
    lesson_completion_age_to_hours: Mapped[int | None] = mapped_column(Integer)
    last_notification_age_from_hours: Mapped[int | None] = mapped_column(Integer)
    last_notification_age_to_hours: Mapped[int | None] = mapped_column(Integer)
    reminders_enabled: Mapped[bool | None] = mapped_column(Boolean)
    has_paid_subscription: Mapped[bool | None] = mapped_column(Boolean)
    registered_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    registered_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_lesson_completed_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_lesson_completed_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_notification_sent_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_notification_sent_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    subscription_statuses: Mapped[list[str] | None] = mapped_column(JSON)
    notifications_enabled: Mapped[bool | None] = mapped_column(Boolean)
    completed_all_lessons: Mapped[bool | None] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(String(256))


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", name="uq_notification_delivery_campaign_user"),
        UniqueConstraint("campaign_id", "user_id", "scheduled_at", name="uq_notification_delivery"),
        Index("ix_notification_delivery_status", "status"),
        Index("ix_notification_delivery_scheduled", "scheduled_at"),
    )

    campaign_id: Mapped[int] = mapped_column(ForeignKey("notification_campaigns.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[NotificationDeliveryStatus] = mapped_column(
        default=NotificationDeliveryStatus.QUEUED,
        server_default=NotificationDeliveryStatus.QUEUED.name,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
