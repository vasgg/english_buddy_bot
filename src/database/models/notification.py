from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import NotificationCampaignStatus, NotificationDeliveryStatus, NotificationSegmentMode


class NotificationCampaign(Base):
    __tablename__ = "notification_campaigns"

    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[NotificationCampaignStatus] = mapped_column(
        default=NotificationCampaignStatus.DRAFT,
        server_default=NotificationCampaignStatus.DRAFT.value,
    )
    message_text: Mapped[str] = mapped_column(Text)
    send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str | None] = mapped_column(String(64))
    is_silent: Mapped[bool | None] = mapped_column(Boolean)


class NotificationSegment(Base):
    __tablename__ = "notification_segments"

    campaign_id: Mapped[int] = mapped_column(ForeignKey("notification_campaigns.id", ondelete="CASCADE"))
    mode: Mapped[NotificationSegmentMode] = mapped_column(
        default=NotificationSegmentMode.EXCLUDE,
        server_default=NotificationSegmentMode.EXCLUDE.value,
    )
    name: Mapped[str | None] = mapped_column(String(128))
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
        UniqueConstraint("campaign_id", "user_id", "scheduled_at", name="uq_notification_delivery"),
        Index("ix_notification_delivery_status", "status"),
        Index("ix_notification_delivery_scheduled", "scheduled_at"),
    )

    campaign_id: Mapped[int] = mapped_column(ForeignKey("notification_campaigns.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[NotificationDeliveryStatus] = mapped_column(
        default=NotificationDeliveryStatus.QUEUED,
        server_default=NotificationDeliveryStatus.QUEUED.value,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
