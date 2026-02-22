import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from PIL import Image
from fastapi import APIRouter, Depends
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from fastui.forms import fastui_form
from sqlalchemy import select

from config import Settings, get_settings
from consts import IMAGE_WIDTH
from database.models.notification import NotificationCampaign, NotificationSegment
from enums import NotificationCampaignMode, NotificationCampaignStatus, NotificationSegmentMode
from webapp.controllers.misc import extract_img_from_form
from webapp.controllers.notifications import get_campaign_preview_count, get_notification_campaigns_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.buttons import back_button
from webapp.routers.components.components import get_common_content
from webapp.schemas.notification import NotificationCampaignForm, NotificationCampaignTableSchema, campaign_form_initial

router = APIRouter()
logger = logging.getLogger()


def _extract_configured_value(condition_enabled: bool, value):
    if not condition_enabled:
        return None
    return value


def _populate_segment_from_form(segment: NotificationSegment, form: NotificationCampaignForm) -> None:
    segment.mode = NotificationSegmentMode.EXCLUDE

    segment.registration_age_from_hours = _extract_configured_value(
        form.use_registration_age,
        form.registration_age_from_hours,
    )
    segment.registration_age_to_hours = _extract_configured_value(
        form.use_registration_age,
        form.registration_age_to_hours,
    )

    segment.inactivity_from_hours = _extract_configured_value(form.use_inactivity, form.inactivity_from_hours)
    segment.inactivity_to_hours = _extract_configured_value(form.use_inactivity, form.inactivity_to_hours)

    segment.lesson_completion_age_from_hours = _extract_configured_value(
        form.use_last_lesson_completion,
        form.lesson_completion_age_from_hours,
    )
    segment.lesson_completion_age_to_hours = _extract_configured_value(
        form.use_last_lesson_completion,
        form.lesson_completion_age_to_hours,
    )

    segment.last_notification_age_from_hours = _extract_configured_value(
        form.use_last_notification_age,
        form.last_notification_age_from_hours,
    )
    segment.last_notification_age_to_hours = _extract_configured_value(
        form.use_last_notification_age,
        form.last_notification_age_to_hours,
    )

    segment.has_paid_subscription = _extract_configured_value(
        form.use_has_paid_subscription,
        form.has_paid_subscription,
    )
    segment.reminders_enabled = _extract_configured_value(form.use_reminders_enabled, form.reminders_enabled)
    segment.completed_all_lessons = _extract_configured_value(
        form.use_completed_all_lessons,
        form.completed_all_lessons,
    )


def _apply_campaign_form(
    campaign: NotificationCampaign,
    form: NotificationCampaignForm,
    *,
    now: datetime,
) -> None:
    campaign.name = form.name
    campaign.message_text = form.message_text
    campaign.mode = form.mode
    campaign.is_silent = form.is_silent
    campaign.send_image_separately = form.send_image_separately
    campaign.check_every_hours = form.check_every_hours if form.mode == NotificationCampaignMode.FILTER else None
    campaign.timer_anchor = form.timer_anchor if form.mode == NotificationCampaignMode.TIMER else None
    campaign.timer_value = form.timer_value if form.mode == NotificationCampaignMode.TIMER else None
    campaign.timer_unit = form.timer_unit if form.mode == NotificationCampaignMode.TIMER else None
    campaign.min_interval_value = form.min_interval_value
    campaign.min_interval_unit = form.min_interval_unit
    if form.is_active:
        if campaign.status != NotificationCampaignStatus.ACTIVE and campaign.activated_at is None:
            campaign.activated_at = now
        campaign.status = NotificationCampaignStatus.ACTIVE
    elif campaign.status == NotificationCampaignStatus.ACTIVE:
        campaign.status = NotificationCampaignStatus.PAUSED


def _save_campaign_image(
    *,
    image_file: bytes | None,
    form: NotificationCampaignForm,
    settings: Settings,
) -> str | None:
    upload = form.upload_new_picture
    if not upload or upload.filename == "":
        return None
    if image_file is None:
        return None

    extension = upload.filename.rsplit(".", 1)[-1].lower()
    if extension not in settings.allowed_image_formats:
        return None

    directory = Path("src/webapp/static/uploaded_notifications/")
    directory.mkdir(parents=True, exist_ok=True)
    image = Image.open(io.BytesIO(image_file))
    if image.width > IMAGE_WIDTH:
        new_height = int((IMAGE_WIDTH / image.width) * image.height)
        image = image.resize((IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    file_name = f"{timestamp}_{upload.filename}"
    file_path = directory / file_name
    with open(file_path, "wb") as buffer:
        image_format = upload.content_type or f"image/{extension}"
        image.save(buffer, format=image_format.split("/")[-1])
    return str(file_path)


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def notifications_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info("notifications router called")
    campaigns = await get_notification_campaigns_table_content(db_session)
    return get_common_content(
        c.Paragraph(
            text=(
                "Важно: если у пользователя не заполнено поле времени (активность/последний урок/последнее уведомление), "
                "то такие условия для него считаются невыполненными, и пользователь не попадет в соответствующую выборку."
            )
        ),
        c.Paragraph(
            text=(
                "Важно по картинкам: при длинном тексте Telegram не позволяет отправить его как caption к фото, "
                "поэтому система автоматически отправит фото и текст отдельными сообщениями."
            )
        ),
        c.Paragraph(text=""),
        c.Div(
            components=[
                c.Button(
                    text="➕ Создать уведомление",
                    named_style="secondary",
                    on_click=GoToEvent(url="/notifications/add/"),
                ),
            ],
        ),
        c.Paragraph(text=""),
        c.Table(
            data=campaigns,
            data_model=NotificationCampaignTableSchema,
            no_data_message="Нет созданных уведомлений",
            columns=[
                DisplayLookup(field="name", title="Название"),
                DisplayLookup(field="mode", title="Режим", table_width_percent=12),
                DisplayLookup(field="status", title="Статус", table_width_percent=10),
                DisplayLookup(field="updated", title="Обработано", table_width_percent=18),
                DisplayLookup(
                    field="preview_button",
                    title=" ",
                    table_width_percent=3,
                    on_click=GoToEvent(url="/notifications/preview/{id}/"),
                ),
                DisplayLookup(
                    field="edit_button",
                    title=" ",
                    table_width_percent=3,
                    on_click=GoToEvent(url="/notifications/edit/{id}/"),
                ),
                DisplayLookup(
                    field="toggle_button",
                    title=" ",
                    table_width_percent=3,
                    on_click=GoToEvent(url="/notifications/toggle/{id}/"),
                ),
            ],
        ),
        title="Настройки уведомлений",
    )


@router.get("/add/", response_model=FastUI, response_model_exclude_none=True)
async def add_notification_page() -> list[AnyComponent]:
    form = c.ModelForm(model=NotificationCampaignForm, submit_url="/api/notifications/add/")
    return get_common_content(
        back_button,
        c.Paragraph(text=""),
        c.Paragraph(
            text=(
                "Подсказка: если включить 'Картинка отдельным сообщением', фото и текст всегда идут двумя сообщениями."
            )
        ),
        c.Paragraph(text=""),
        form,
        title="Создать уведомление",
    )


@router.post("/add/", response_model=FastUI, response_model_exclude_none=True)
async def add_notification(
    image_file: Annotated[bytes | None, Depends(extract_img_from_form)],
    db_session: AsyncDBSession,
    form: Annotated[NotificationCampaignForm, fastui_form(NotificationCampaignForm)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[AnyComponent]:
    now = datetime.now(timezone.utc)
    campaign = NotificationCampaign(
        name=form.name,
        message_text=form.message_text,
    )
    _apply_campaign_form(campaign, form, now=now)
    new_image_path = _save_campaign_image(image_file=image_file, form=form, settings=settings)
    if new_image_path is not None:
        campaign.image_path = new_image_path

    db_session.add(campaign)
    await db_session.flush()

    segment = NotificationSegment(campaign_id=campaign.id)
    _populate_segment_from_form(segment, form)
    db_session.add(segment)
    await db_session.flush()

    return [c.FireEvent(event=GoToEvent(url="/notifications"))]


@router.get("/edit/{campaign_id}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_notification_page(campaign_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    campaign = await db_session.get(NotificationCampaign, campaign_id)
    assert campaign is not None
    segment_query = select(NotificationSegment).filter(NotificationSegment.campaign_id == campaign_id)
    segment = (await db_session.execute(segment_query)).scalars().first()

    initial = campaign_form_initial(campaign, segment)
    form = c.ModelForm(
        model=NotificationCampaignForm,
        submit_url=f"/api/notifications/edit/{campaign_id}/",
        initial=initial,
    )
    image_line = c.Paragraph(
        text=f"Текущее изображение: {campaign.image_path}" if campaign.image_path else "Изображение: нет"
    )
    return get_common_content(
        back_button,
        c.Paragraph(text=""),
        c.Paragraph(
            text=("Подсказка: пользователи с пустыми timestamp-полями не пройдут условия, завязанные на эти поля.")
        ),
        c.Paragraph(text=""),
        image_line,
        c.Paragraph(text=""),
        form,
        title=f"Редактировать уведомление #{campaign_id}",
    )


@router.post("/edit/{campaign_id}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_notification(
    campaign_id: int,
    image_file: Annotated[bytes | None, Depends(extract_img_from_form)],
    db_session: AsyncDBSession,
    form: Annotated[NotificationCampaignForm, fastui_form(NotificationCampaignForm)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[AnyComponent]:
    now = datetime.now(timezone.utc)
    campaign = await db_session.get(NotificationCampaign, campaign_id)
    assert campaign is not None

    _apply_campaign_form(campaign, form, now=now)
    new_image_path = _save_campaign_image(image_file=image_file, form=form, settings=settings)
    if new_image_path is not None:
        campaign.image_path = new_image_path

    segment_query = select(NotificationSegment).filter(NotificationSegment.campaign_id == campaign_id)
    segment = (await db_session.execute(segment_query)).scalars().first()
    if segment is None:
        segment = NotificationSegment(campaign_id=campaign_id)
        db_session.add(segment)

    _populate_segment_from_form(segment, form)
    await db_session.flush()
    return [c.FireEvent(event=GoToEvent(url="/notifications"))]


@router.get("/toggle/{campaign_id}/", response_model=FastUI, response_model_exclude_none=True)
async def toggle_notification(campaign_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    campaign = await db_session.get(NotificationCampaign, campaign_id)
    assert campaign is not None
    now = datetime.now(timezone.utc)
    if campaign.status == NotificationCampaignStatus.ACTIVE:
        campaign.status = NotificationCampaignStatus.PAUSED
    else:
        if campaign.activated_at is None:
            campaign.activated_at = now
        campaign.status = NotificationCampaignStatus.ACTIVE
    await db_session.flush()
    return [c.FireEvent(event=GoToEvent(url="/notifications"))]


@router.get("/preview/{campaign_id}/", response_model=FastUI, response_model_exclude_none=True)
async def preview_notification(campaign_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    count = await get_campaign_preview_count(campaign_id, db_session)
    return get_common_content(
        back_button,
        c.Paragraph(text=""),
        c.Heading(text=f"Получателей сейчас: {count}", level=4),
        c.Paragraph(text="В preview учитываются текущие фильтры, одноразовость по кампании и cooldown."),
        title=f"Предпросмотр #{campaign_id}",
    )
