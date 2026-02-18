"""initial

Revision ID: 20260217_0001
Revises: 
Create Date: 2026-02-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

from enums import (
    KeyboardType,
    LessonLevel,
    LessonStatus,
    NotificationCampaignStatus,
    NotificationDeliveryStatus,
    NotificationSegmentMode,
    ReactionType,
    SessionStartsFrom,
    SessionStatus,
    SlideType,
    StickerType,
    UserSubscriptionType,
)


revision = "20260217_0001"
down_revision = None
branch_labels = None
depends_on = None


def _enum_types() -> dict[str, sa.Enum]:
    return {
        # Use Postgres ENUM with create_type=False so we can safely create types
        # once (with checkfirst=True) and avoid a duplicate CREATE TYPE during
        # table creation.
        "keyboardtype": ENUM(KeyboardType, name="keyboardtype", create_type=False),
        "lessonlevel": ENUM(LessonLevel, name="lessonlevel", create_type=False),
        "lessonstatus": ENUM(LessonStatus, name="lessonstatus", create_type=False),
        "notificationcampaignstatus": ENUM(
            NotificationCampaignStatus, name="notificationcampaignstatus", create_type=False
        ),
        "notificationdeliverystatus": ENUM(
            NotificationDeliveryStatus, name="notificationdeliverystatus", create_type=False
        ),
        "notificationsegmentmode": ENUM(NotificationSegmentMode, name="notificationsegmentmode", create_type=False),
        "reactiontype": ENUM(ReactionType, name="reactiontype", create_type=False),
        "sessionstartsfrom": ENUM(SessionStartsFrom, name="sessionstartsfrom", create_type=False),
        "sessionstatus": ENUM(SessionStatus, name="sessionstatus", create_type=False),
        "slidetype": ENUM(SlideType, name="slidetype", create_type=False),
        "stickertype": ENUM(StickerType, name="stickertype", create_type=False),
        "usersubscriptiontype": ENUM(UserSubscriptionType, name="usersubscriptiontype", create_type=False),
    }


def _drop_enum_types(bind, enums: dict[str, sa.Enum]) -> None:
    for enum in enums.values():
        enum.drop(bind, checkfirst=True)


def upgrade() -> None:
    bind = op.get_bind()
    enums = _enum_types()
    for enum in enums.values():
        enum.create(bind, checkfirst=True)

    op.create_table(
        "lessons",
        sa.Column("index", sa.Integer(), nullable=True, unique=True),
        sa.Column("title", sa.String(), nullable=False, server_default="NEW LESSON TEMPLATE"),
        sa.Column("level", enums["lessonlevel"], nullable=True),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("path_extra", sa.String(), nullable=True),
        sa.Column("errors_threshold", sa.Integer(), nullable=True),
        sa.Column("is_active", enums["lessonstatus"], nullable=False, server_default="EDITING"),
        sa.Column("is_paid", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("fullname", sa.String(), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=True),
        sa.Column("reminder_freq", sa.Integer(), nullable=True),
        sa.Column("last_reminded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_lesson_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("completed_lessons_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_all_lessons", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "subscription_status",
            enums["usersubscriptiontype"],
            nullable=False,
            server_default=UserSubscriptionType.NO_ACCESS.value,
        ),
        sa.Column("subscription_expired_at", sa.Date(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "texts",
        sa.Column("prompt", sa.String(), nullable=False, unique=True),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "reactions",
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("type", enums["reactiontype"], nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "stickers",
        sa.Column("sticker_id", sa.String(), nullable=False, unique=True),
        sa.Column("sticker_type", enums["stickertype"], nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "reminder_text_variants",
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "notification_campaigns",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            enums["notificationcampaignstatus"],
            nullable=False,
            server_default=NotificationCampaignStatus.DRAFT.value,
        ),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("send_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("is_silent", sa.Boolean(), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "notification_segments",
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column(
            "mode",
            enums["notificationsegmentmode"],
            nullable=False,
            server_default=NotificationSegmentMode.EXCLUDE.value,
        ),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("registered_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registered_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_lesson_completed_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_lesson_completed_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notification_sent_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notification_sent_after", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subscription_statuses", sa.JSON(), nullable=True),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=True),
        sa.Column("completed_all_lessons", sa.Boolean(), nullable=True),
        sa.Column("comment", sa.String(length=256), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["notification_campaigns.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "sessions",
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("path_extra", sa.String(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_from", enums["sessionstartsfrom"], nullable=False),
        sa.Column("status", enums["sessionstatus"], nullable=False, server_default=SessionStatus.IN_PROGRESS.value),
        sa.Column("in_extra", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "slides",
        sa.Column("text", sa.String(), nullable=True),
        sa.Column("picture", sa.String(), nullable=True),
        sa.Column("delay", sa.Float(), nullable=True),
        sa.Column("slide_type", enums["slidetype"], nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("right_answers", sa.String(), nullable=True),
        sa.Column("almost_right_answers", sa.String(), nullable=True),
        sa.Column("almost_right_answer_reply", sa.String(), nullable=True),
        sa.Column("keyboard_type", enums["keyboardtype"], nullable=True),
        sa.Column("keyboard", sa.String(), nullable=True),
        sa.Column("is_exam_slide", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "quiz_answer_logs",
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("slide_id", sa.Integer(), nullable=False),
        sa.Column("slide_type", enums["slidetype"], nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slide_id"], ["slides.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            enums["notificationdeliverystatus"],
            nullable=False,
            server_default=NotificationDeliveryStatus.QUEUED.value,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["notification_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("campaign_id", "user_id", "scheduled_at", name="uq_notification_delivery"),
    )
    op.create_index("ix_notification_delivery_status", "notification_deliveries", ["status"])
    op.create_index("ix_notification_delivery_scheduled", "notification_deliveries", ["scheduled_at"])


def downgrade() -> None:
    bind = op.get_bind()
    enums = _enum_types()

    op.drop_index("ix_notification_delivery_scheduled", table_name="notification_deliveries")
    op.drop_index("ix_notification_delivery_status", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
    op.drop_table("quiz_answer_logs")
    op.drop_table("slides")
    op.drop_table("sessions")
    op.drop_table("notification_segments")
    op.drop_table("notification_campaigns")
    op.drop_table("reminder_text_variants")
    op.drop_table("stickers")
    op.drop_table("reactions")
    op.drop_table("texts")
    op.drop_table("users")
    op.drop_table("lessons")

    _drop_enum_types(bind, enums)
