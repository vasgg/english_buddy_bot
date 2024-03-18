import logging
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent
from fastui.forms import fastui_form

from webapp.controllers.text import get_text_by_id, get_texts_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.components import get_common_content
from webapp.schemas.text import EditTextDataModel, get_text_data_model

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def texts_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('texts router called')
    texts = await get_texts_table_content(db_session)
    return get_common_content(
        # c.Div(components=components_right),
        c.Paragraph(text=''),
        c.Table(
            data=texts,
            columns=[
                # DisplayLookup(field='id', table_width_percent=3, on_click=GoToEvent(url='/reactions/{id}/')),
                DisplayLookup(field='description', title='description'),
                DisplayLookup(field='text', title='text'),
                DisplayLookup(
                    field='edit_button',
                    title=' ',
                    on_click=GoToEvent(url='/texts/edit/{id}'),
                    table_width_percent=3,
                ),
            ],
            # class_name='text-decoration-none',
        ),
        c.Paragraph(text=''),
        title='Тексты',
    )


@router.get("/edit/{text_id}", response_model=FastUI, response_model_exclude_none=True)
async def edit_text_page(text_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    text = await get_text_by_id(text_id, db_session)
    submit_url = f'/api/texts/edit/{text_id}/'
    form = c.ModelForm(model=get_text_data_model(text), submit_url=submit_url)
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
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
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(text, field, form_value)
    await db_session.commit()
    logger.info(f'text {text.id} updated. data: {form.dict()}')
    return [c.FireEvent(event=GoToEvent(url=f'/texts'))]
