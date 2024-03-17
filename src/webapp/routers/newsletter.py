import io
import logging
from pathlib import Path
from typing import Annotated

from PIL import Image
from fastapi import APIRouter, Depends
from fastui import AnyComponent, FastUI, components as c
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from config import settings
from database.crud.user import get_all_users_with_reminders
from database.db import AsyncDBSession
from database.schemas.newsletter import get_newsletter_data_model
from webapp.controllers.misc import extract_img_from_form, send_newsletter_to_users
from webapp.routers.components import get_common_content

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def newsletter_page() -> list[AnyComponent]:
    logger.info('newsletter router called')
    submit_url = '/api/newsletter/send/'
    form = c.ModelForm(model=get_newsletter_data_model(), submit_url=submit_url)
    return get_common_content(
        c.Paragraph(text=''),
        form,
        c.Paragraph(text=''),
        title='Рассылка',
    )


@router.get("/sent/", response_model=FastUI, response_model_exclude_none=True)
async def newsletter_page() -> list[AnyComponent]:
    return get_common_content(
        c.Paragraph(text=''),
        c.Paragraph(text=''),
        title='Рассылка отправлена!',
    )


@router.post('/send/', response_model=FastUI, response_model_exclude_none=True)
async def send_newsletter(
    image_file: Annotated[bytes, Depends(extract_img_from_form)],
    db_session: AsyncDBSession,
    form: Annotated[get_newsletter_data_model(), fastui_form(get_newsletter_data_model())],
) -> list[AnyComponent]:
    users_with_reminders = [user.telegram_id for user in await get_all_users_with_reminders(db_session)]
    text = form.text
    if form.upload_new_picture.filename != '':
        if form.upload_new_picture.filename.rsplit('.', 1)[1].lower() in settings.allowed_image_formats:
            directory = Path(f"src/webapp/static/uploaded_images/")
            directory.mkdir(parents=True, exist_ok=True)
            image = Image.open(io.BytesIO(image_file))
            if image.width > 800:
                new_height = int((800 / image.width) * image.height)
                image = image.resize((800, new_height), Image.Resampling.LANCZOS)
            file_path = directory / form.upload_new_picture.filename
            with open(file_path, "wb") as buffer:
                image_format = form.upload_new_picture.content_type
                image.save(buffer, format=image_format.split("/")[1])
            await send_newsletter_to_users(users_with_reminders, text, file_path)

    else:
        await send_newsletter_to_users(users_with_reminders, text)
    return [c.FireEvent(event=GoToEvent(url='/newsletter/sent/'))]
