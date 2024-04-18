import logging
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from database.models.reaction import Reaction
from enums import ReactionType
from webapp.controllers.reaction import delete_reaction_by_id, get_reaction_by_id, get_reactions_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.main_component import back_button, get_common_content
from webapp.schemas.reaction import (
    AddReactionDataModel,
    EditReactionDataModel,
    get_new_reaction_data_model,
    get_reaction_data_model,
)

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    right_reactions = await get_reactions_table_content(ReactionType.RIGHT, db_session)
    wrong_reactions = await get_reactions_table_content(ReactionType.WRONG, db_session)
    return get_common_content(
        c.Div(
            components=[
                c.Heading(text='RIGHT', level=4),
                c.Button(text='➕', named_style='secondary', on_click=GoToEvent(url='/reactions/add/right/')),
            ],
        ),
        c.Paragraph(text=''),
        c.Table(
            data=right_reactions,
            columns=[
                DisplayLookup(field='text', title='text'),
                DisplayLookup(
                    field='edit_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/edit/{id}'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='minus_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/confirm_delete/{id}/'),
                    table_width_percent=3,
                ),
            ],
        ),
        c.Paragraph(text=''),
        c.Div(
            components=[
                c.Heading(text='WRONG', level=4),
                c.Button(
                    text='➕',
                    named_style='secondary',
                    on_click=GoToEvent(url='/reactions/add/wrong/'),
                ),
            ],
        ),
        c.Paragraph(text=''),
        c.Table(
            data=wrong_reactions,
            columns=[
                DisplayLookup(field='text', title='text'),
                DisplayLookup(
                    field='edit_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/edit/{id}'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='minus_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/confirm_delete/{id}/'),
                    table_width_percent=3,
                ),
            ],
        ),
        title='Реакции',
    )


@router.get('/add/{reaction_type}/', response_model=FastUI, response_model_exclude_none=True)
async def add_reaction_form(reaction_type: ReactionType) -> list[AnyComponent]:
    match reaction_type:
        case ReactionType.RIGHT:
            submit_url = '/api/reactions/add/right/'
            form = c.ModelForm(
                model=get_new_reaction_data_model(reaction_type=ReactionType.RIGHT),
                submit_url=submit_url,
            )
        case ReactionType.WRONG:
            submit_url = '/api/reactions/add/wrong/'
            form = c.ModelForm(
                model=get_new_reaction_data_model(reaction_type=ReactionType.WRONG),
                submit_url=submit_url,
            )
        case _:
            raise AssertionError("Unexpected reaction type")
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title=f'add reaction | {reaction_type.value}',
    )


@router.post('/add/{reaction_type}/', response_model=FastUI, response_model_exclude_none=True)
async def add_reaction(
    reaction_type: ReactionType,
    db_session: AsyncDBSession,
    form: Annotated[AddReactionDataModel, fastui_form(AddReactionDataModel)],
):
    reaction = Reaction(type=reaction_type, text=form.text)
    db_session.add(reaction)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url='/reactions'))]


@router.post('/delete/{reaction_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_reaction(
    reaction_id: int,
    db_session: AsyncDBSession,
):
    await delete_reaction_by_id(reaction_id, db_session)
    return [c.FireEvent(event=GoToEvent(url='/reactions'))]


@router.get("/edit/{reaction_id}", response_model=FastUI, response_model_exclude_none=True)
async def edit_text_page(reaction_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    reaction = await get_reaction_by_id(reaction_id, db_session)
    submit_url = f'/api/reactions/edit/{reaction_id}/'
    form = c.ModelForm(model=get_reaction_data_model(reaction), submit_url=submit_url)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title=f'edit | reaction {reaction_id}',
    )


@router.post('/edit/{reaction_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_lesson_form(
    reaction_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditReactionDataModel, fastui_form(EditReactionDataModel)],
):
    reaction = await get_reaction_by_id(reaction_id, db_session)
    for field in form.model_fields:
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(reaction, field, form_value)
    await db_session.commit()
    logger.info(f'reaction {reaction.id} updated. data: {form.dict()}')
    return [c.FireEvent(event=GoToEvent(url='/reactions'))]


@router.get('/confirm_delete/{reaction_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_slide(reaction_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    reaction: Reaction = await get_reaction_by_id(reaction_id, db_session)
    return get_common_content(
        c.Paragraph(text=''),
        c.Heading(text=f'{reaction.text}', level=4),
        c.Paragraph(text='Вы уверены, что хотите удалить эту реакцию?'),
        c.Div(
            components=[
                back_button,
                c.Link(
                    components=[c.Button(text='Удалить', named_style='warning')],
                    on_click=GoToEvent(url=f'/reactions/delete/{reaction_id}/'),
                    class_name='+ ms-2',
                ),
            ],
        ),
        title=f'delete | reaction {reaction_id}',
    )


@router.get('/delete/{reaction_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_slide_response(
    reaction_id: int,
    db_session: AsyncDBSession,
):
    logger.info(f'reaction with id {reaction_id} deleted')
    await delete_reaction_by_id(reaction_id, db_session)
    return [c.FireEvent(event=GoToEvent(url='/reactions'))]
