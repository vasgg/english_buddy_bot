from __future__ import annotations

from datetime import datetime, timezone
import logging

from sqlalchemy import select

from database.models.notification import NotificationCampaign, NotificationDelivery, NotificationSegment
from database.models.user import User
from enums import NotificationCampaignMode
from notifications.engine import (
    campaign_timer_delay,
    ensure_utc,
    timer_anchor_dt,
    user_matches_exclusion_segment,
    user_passes_campaign_min_interval,
)
from webapp.db import AsyncDBSession
from webapp.schemas.notification import NotificationCampaignTableSchema

logger = logging.getLogger()


def _mode_label(mode: NotificationCampaignMode) -> str:
    if mode == NotificationCampaignMode.TIMER:
        return "Таймер"
    return "Фильтр"


def _status_label(status) -> str:
    status_str = str(status).split(".")[-1]
    return status_str.lower()


async def get_notification_campaigns_table_content(
    db_session: AsyncDBSession,
) -> list[NotificationCampaignTableSchema]:
    campaigns_query = select(NotificationCampaign).order_by(NotificationCampaign.created_at.desc())
    campaigns = list((await db_session.execute(campaigns_query)).scalars().all())

    rows: list[NotificationCampaignTableSchema] = []
    for campaign in campaigns:
        updated = "—"
        if campaign.last_processed_at is not None:
            updated_at = ensure_utc(campaign.last_processed_at)
            assert updated_at is not None
            updated = updated_at.strftime("%Y-%m-%d %H:%M UTC")

        row = NotificationCampaignTableSchema.model_validate(
            {
                "id": campaign.id,
                "name": campaign.name,
                "mode": _mode_label(campaign.mode),
                "status": _status_label(campaign.status),
                "updated": updated,
                "preview_button": "👁",
                "edit_button": "✏️",
                "toggle_button": "⏸" if _status_label(campaign.status) == "active" else "▶️",
            }
        )
        rows.append(row)

    logger.info("processed %s notification campaigns", len(rows))
    return rows


async def get_campaign_preview_count(campaign_id: int, db_session: AsyncDBSession) -> int:
    campaign = await db_session.get(NotificationCampaign, campaign_id)
    if campaign is None:
        return 0

    segment_query = select(NotificationSegment).filter(NotificationSegment.campaign_id == campaign_id)
    segment = (await db_session.execute(segment_query)).scalars().first()

    users_query = select(User)
    users = list((await db_session.execute(users_query)).scalars().all())

    processed_query = select(NotificationDelivery.user_id).filter(NotificationDelivery.campaign_id == campaign_id)
    processed_user_ids = set((await db_session.execute(processed_query)).scalars().all())

    now = datetime.now(timezone.utc)
    if campaign.mode == NotificationCampaignMode.FILTER:
        count = 0
        for user in users:
            if user.id in processed_user_ids:
                continue
            if user_matches_exclusion_segment(user, segment, now=now):
                continue
            if not user_passes_campaign_min_interval(user, campaign, now=now):
                continue
            count += 1
        return count

    delay = campaign_timer_delay(campaign)
    if delay is None or campaign.timer_anchor is None:
        return 0

    activated_at = ensure_utc(campaign.activated_at) or ensure_utc(campaign.created_at)
    assert activated_at is not None
    count = 0
    for user in users:
        if user.id in processed_user_ids:
            continue
        anchor_dt = timer_anchor_dt(user, campaign)
        if anchor_dt is None:
            continue
        due_at = anchor_dt + delay
        if due_at < activated_at:
            continue
        if due_at > now:
            continue
        if user_matches_exclusion_segment(user, segment, now=now):
            continue
        if not user_passes_campaign_min_interval(user, campaign, now=now):
            continue
        count += 1
    return count
