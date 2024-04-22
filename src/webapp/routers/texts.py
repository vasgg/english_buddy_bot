import logging
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from webapp.controllers.text import get_text_by_id, get_texts_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.buttons import back_button
from webapp.routers.components.components import get_common_content, get_texts_page
from webapp.schemas.text import EditTextDataModel, get_text_data_model

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def texts_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('texts router called')
    texts = await get_texts_table_content(db_session)
    return get_texts_page(texts)


@router.get("/edit/{text_id}", response_model=FastUI, response_model_exclude_none=True)
async def edit_text_page(text_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    text = await get_text_by_id(text_id, db_session)
    submit_url = f'/api/texts/edit/{text_id}/'
    form = c.ModelForm(model=get_text_data_model(text), submit_url=submit_url)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title=f'edit | text {text_id}',
    )


@router.post('/edit/{text_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_text_form(
    text_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditTextDataModel, fastui_form(EditTextDataModel)],
):
    text = await get_text_by_id(text_id, db_session)
    for field in form.model_fields:
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(text, field, form_value)
    logger.info(f'text {text.id} updated. data: {form.dict()}')
    return [c.FireEvent(event=GoToEvent(url='/texts'))]
