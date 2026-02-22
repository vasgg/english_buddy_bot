from datetime import datetime, timezone

from sqlalchemy import select

from database.models.notification import NotificationCampaign, NotificationSegment
from database.models.user import User
from enums import NotificationCampaignMode
from webapp.controllers.notifications import get_campaign_preview_count


async def test_notifications_page_handles_empty_campaigns(client):
    response = await client.get("/api/notifications")
    assert response.status_code == 200


async def test_add_notification_campaign_via_api_creates_campaign_and_segment(client, db):
    payload = {
        "name": "Retention campaign",
        "message_text": "Hello!",
        "mode": NotificationCampaignMode.FILTER.value,
        "is_active": "true",
        "is_silent": "true",
        "send_image_separately": "false",
        "check_every_hours": "6",
    }
    response = await client.post("/api/notifications/add/", data=payload)
    assert response.status_code == 200

    async with db.session_factory() as session:
        campaigns = list((await session.execute(select(NotificationCampaign))).scalars().all())
        segments = list((await session.execute(select(NotificationSegment))).scalars().all())

    assert len(campaigns) == 1
    assert campaigns[0].name == "Retention campaign"
    assert campaigns[0].mode == NotificationCampaignMode.FILTER
    assert len(segments) == 1
    assert segments[0].campaign_id == campaigns[0].id


async def test_preview_count_excludes_users_without_required_timestamp(db):
    async with db.session_factory.begin() as session:
        session.add(
            User(
                telegram_id=101,
                fullname="No Activity",
                username="no_activity",
                last_reminded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                last_activity_at=None,
            )
        )
        campaign = NotificationCampaign(
            name="Inactivity campaign",
            message_text="Ping",
            mode=NotificationCampaignMode.FILTER,
            check_every_hours=24,
        )
        session.add(campaign)
        await session.flush()

        segment = NotificationSegment(
            campaign_id=campaign.id,
            inactivity_from_hours=24,
            inactivity_to_hours=24 * 30,
        )
        session.add(segment)

    async with db.session_factory() as session:
        count = await get_campaign_preview_count(campaign.id, session)

    # Seed user in tests has no last_activity_at -> excluded from inactivity condition evaluation.
    assert count == 0
