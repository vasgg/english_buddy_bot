import logging
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from database.models.reminder_text_variant import ReminderTextVariant
from webapp.controllers.reminder_texts import (
    delete_reminder_text_variant_by_id,
    get_reminder_text_variant_by_id,
    get_reminder_text_variants_table_content,
)
from webapp.db import AsyncDBSession
from webapp.routers.components.buttons import back_button
from webapp.routers.components.components import get_common_content
from webapp.routers.components.tables import get_reminder_texts_table
from webapp.schemas.reminder_texts import (
    AddReminderTextVariantDataModel,
    EditReminderTextVariantDataModel,
    get_new_reminder_text_variant_data_model,
    get_reminder_text_variant_data_model,
)

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def reminder_texts_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('reminder_texts router called')
    variants = await get_reminder_text_variants_table_content(db_session)
    return get_common_content(
        c.Div(
            components=[
                c.Heading(text='Reminder texts', level=4),
                c.Button(text='➕', named_style='secondary', on_click=GoToEvent(url='/reminder_texts/add/')),
            ],
        ),
        c.Paragraph(text=''),
        get_reminder_texts_table(variants),
        title='Тексты напоминаний',
    )


@router.get('/add/', response_model=FastUI, response_model_exclude_none=True)
async def add_reminder_text_form() -> list[AnyComponent]:
    submit_url = '/api/reminder_texts/add/'
    form = c.ModelForm(model=get_new_reminder_text_variant_data_model(), submit_url=submit_url)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title='add | reminder text',
    )


@router.post('/add/', response_model=FastUI, response_model_exclude_none=True)
async def add_reminder_text(
    db_session: AsyncDBSession,
    form: Annotated[AddReminderTextVariantDataModel, fastui_form(AddReminderTextVariantDataModel)],
):
    variant = ReminderTextVariant(text=form.text)
    db_session.add(variant)
    return [c.FireEvent(event=GoToEvent(url='/reminder_texts'))]


@router.get("/edit/{variant_id}", response_model=FastUI, response_model_exclude_none=True)
async def edit_reminder_text_page(variant_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    variant = await get_reminder_text_variant_by_id(variant_id, db_session)
    submit_url = f'/api/reminder_texts/edit/{variant_id}/'
    form = c.ModelForm(model=get_reminder_text_variant_data_model(variant), submit_url=submit_url)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title=f'edit | reminder text {variant_id}',
    )


@router.post('/edit/{variant_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_reminder_text_form(
    variant_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditReminderTextVariantDataModel, fastui_form(EditReminderTextVariantDataModel)],
):
    variant = await get_reminder_text_variant_by_id(variant_id, db_session)
    for field in form.model_fields:
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(variant, field, form_value)
    logger.info('reminder text %s updated. data: %s', variant.id, form.dict())
    return [c.FireEvent(event=GoToEvent(url='/reminder_texts'))]


@router.get('/confirm_delete/{variant_id}/', response_model=FastUI, response_model_exclude_none=True)
async def confirm_delete_reminder_text(variant_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    variant = await get_reminder_text_variant_by_id(variant_id, db_session)
    return get_common_content(
        c.Paragraph(text=''),
        c.Heading(text=f'{variant.text}', level=4),
        c.Paragraph(text='Вы уверены, что хотите удалить этот вариант?'),
        c.Div(
            components=[
                back_button,
                c.Link(
                    components=[c.Button(text='Удалить', named_style='warning')],
                    on_click=GoToEvent(url=f'/reminder_texts/delete/{variant_id}/'),
                    class_name='+ ms-2',
                ),
            ],
        ),
        title=f'delete | reminder text {variant_id}',
    )


@router.get('/delete/{variant_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_reminder_text_response(
    variant_id: int,
    db_session: AsyncDBSession,
):
    logger.info('reminder text with id %s deleted', variant_id)
    await delete_reminder_text_variant_by_id(variant_id, db_session)
    return [c.FireEvent(event=GoToEvent(url='/reminder_texts'))]

