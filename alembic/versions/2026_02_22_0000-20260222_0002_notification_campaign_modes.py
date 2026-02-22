"""notification campaign modes and filters

Revision ID: 20260222_0002
Revises: 20260217_0001
Create Date: 2026-02-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

from enums import NotificationCampaignMode, NotificationTimeUnit, NotificationTimerAnchor


revision = "20260222_0002"
down_revision = "20260217_0001"
branch_labels = None
depends_on = None


def _enum_types() -> dict[str, sa.Enum]:
    return {
        "notificationcampaignmode": ENUM(NotificationCampaignMode, name="notificationcampaignmode", create_type=False),
        "notificationtimeranchor": ENUM(NotificationTimerAnchor, name="notificationtimeranchor", create_type=False),
        "notificationtimeunit": ENUM(NotificationTimeUnit, name="notificationtimeunit", create_type=False),
    }


def _drop_enum_types(bind, enums: dict[str, sa.Enum]) -> None:
    for enum in enums.values():
        enum.drop(bind, checkfirst=True)


def upgrade() -> None:
    bind = op.get_bind()
    enums = _enum_types()
    for enum in enums.values():
        enum.create(bind, checkfirst=True)

    op.add_column(
        "notification_campaigns",
        sa.Column(
            "mode",
            enums["notificationcampaignmode"],
            nullable=False,
            server_default=NotificationCampaignMode.FILTER.name,
        ),
    )
    op.add_column("notification_campaigns", sa.Column("check_every_hours", sa.Integer(), nullable=True))
    op.add_column(
        "notification_campaigns",
        sa.Column("timer_anchor", enums["notificationtimeranchor"], nullable=True),
    )
    op.add_column("notification_campaigns", sa.Column("timer_value", sa.Integer(), nullable=True))
    op.add_column(
        "notification_campaigns",
        sa.Column("timer_unit", enums["notificationtimeunit"], nullable=True),
    )
    op.add_column("notification_campaigns", sa.Column("min_interval_value", sa.Integer(), nullable=True))
    op.add_column(
        "notification_campaigns",
        sa.Column("min_interval_unit", enums["notificationtimeunit"], nullable=True),
    )
    op.add_column("notification_campaigns", sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notification_campaigns", sa.Column("last_processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notification_campaigns", sa.Column("image_path", sa.String(length=512), nullable=True))
    op.add_column(
        "notification_campaigns",
        sa.Column("send_image_separately", sa.Boolean(), nullable=False, server_default="0"),
    )

    op.add_column("notification_segments", sa.Column("registration_age_from_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("registration_age_to_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("inactivity_from_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("inactivity_to_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("lesson_completion_age_from_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("lesson_completion_age_to_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("last_notification_age_from_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("last_notification_age_to_hours", sa.Integer(), nullable=True))
    op.add_column("notification_segments", sa.Column("reminders_enabled", sa.Boolean(), nullable=True))
    op.add_column("notification_segments", sa.Column("has_paid_subscription", sa.Boolean(), nullable=True))

    op.create_unique_constraint(
        "uq_notification_delivery_campaign_user",
        "notification_deliveries",
        ["campaign_id", "user_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    enums = _enum_types()

    op.drop_constraint("uq_notification_delivery_campaign_user", "notification_deliveries", type_="unique")

    op.drop_column("notification_segments", "has_paid_subscription")
    op.drop_column("notification_segments", "reminders_enabled")
    op.drop_column("notification_segments", "last_notification_age_to_hours")
    op.drop_column("notification_segments", "last_notification_age_from_hours")
    op.drop_column("notification_segments", "lesson_completion_age_to_hours")
    op.drop_column("notification_segments", "lesson_completion_age_from_hours")
    op.drop_column("notification_segments", "inactivity_to_hours")
    op.drop_column("notification_segments", "inactivity_from_hours")
    op.drop_column("notification_segments", "registration_age_to_hours")
    op.drop_column("notification_segments", "registration_age_from_hours")

    op.drop_column("notification_campaigns", "image_path")
    op.drop_column("notification_campaigns", "send_image_separately")
    op.drop_column("notification_campaigns", "last_processed_at")
    op.drop_column("notification_campaigns", "activated_at")
    op.drop_column("notification_campaigns", "min_interval_unit")
    op.drop_column("notification_campaigns", "min_interval_value")
    op.drop_column("notification_campaigns", "timer_unit")
    op.drop_column("notification_campaigns", "timer_value")
    op.drop_column("notification_campaigns", "timer_anchor")
    op.drop_column("notification_campaigns", "check_every_hours")
    op.drop_column("notification_campaigns", "mode")

    _drop_enum_types(bind, enums)
