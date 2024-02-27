from asyncio import sleep
import logging
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent, PageEvent
from fastui.forms import fastui_form

from bot.resources.enums import ReactionType
from controllers.reaction import delete_reaction_by_id, get_reaction_by_id, get_reactions_table_content
from database.db import AsyncDBSession
from database.schemas.reaction import EditReactionDataModel, get_reaction_data_model
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get("", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    right_reactions = await get_reactions_table_content(ReactionType.RIGHT, db_session)
    wrong_reactions = await get_reactions_table_content(ReactionType.WRONG, db_session)
    return get_common_content(
        c.Div(
            components=[
                c.Heading(text='RIGHT', level=4),
                c.Button(text='➕', named_style='secondary', on_click=GoToEvent(url=f'/slides/{777}/')),
            ]
        ),
        # c.Div(components=components_right),
        c.Paragraph(text=''),
        c.Table(
            data=right_reactions,
            columns=[
                # DisplayLookup(field='id', table_width_percent=3, on_click=GoToEvent(url='/reactions/{id}/')),
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
                    on_click=PageEvent(name='modal-prompt'),
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
                    on_click=GoToEvent(url=f'/slides/{777}/'),
                ),
            ]
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
                    on_click=PageEvent(name='modal-prompt'),
                    table_width_percent=3,
                ),
            ],
        ),
        c.Modal(
            title='Удаление реакции',
            body=[
                c.Paragraph(text='Вы действительно хотите удалить реакцию?'),
                c.Form(
                    form_fields=[],
                    submit_url='/api/reactions/modal-prompt/',
                    loading=[c.Spinner(text=f'Deleting reaction...')],
                    footer=[],
                    submit_trigger=PageEvent(name='modal-form-submit'),
                ),
            ],
            footer=[
                c.Button(text='Cancel', named_style='secondary', on_click=PageEvent(name='modal-prompt', clear=True)),
                c.Button(text='Submit', on_click=PageEvent(name='modal-form-submit')),
            ],
            open_trigger=PageEvent(name='modal-prompt'),
        ),
        title='Реакции',
    )


@app.post('/modal-prompt/', response_model=FastUI, response_model_exclude_none=True)
async def modal_prompt_submit() -> list[AnyComponent]:
    await sleep(0.5)
    # reaction_id = event.context.get('reaction_id')

    print(f'deleting reaction...')

    # await delete_reaction_by_id()
    return [c.FireEvent(event=PageEvent(name='modal-prompt', clear=True))]


@app.post('/delete/{reaction_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_reaction(
    reaction_id: int,
    db_session: AsyncDBSession,
):
    await delete_reaction_by_id(reaction_id, db_session)
    return [c.FireEvent(event=GoToEvent(url=f'/reactions'))]


@app.get("/edit/{reaction_id}", response_model=FastUI, response_model_exclude_none=True)
async def edit_text_page(reaction_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    reaction = await get_reaction_by_id(reaction_id, db_session)
    submit_url = f'/api/reactions/edit/{reaction_id}/'
    form = c.ModelForm(model=get_reaction_data_model(reaction), submit_url=submit_url)
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=''),
        form,
        title=f'edit | reaction {reaction_id}',
    )


@app.post('/edit/{reaction_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_lesson_form(
    reaction_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditReactionDataModel, fastui_form(EditReactionDataModel)],
):
    reaction = await get_reaction_by_id(reaction_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(reaction, field, form_value)
    await db_session.commit()
    logger.info(f'reaction {reaction.id} updated. data: {form.dict()}')
    return [c.FireEvent(event=GoToEvent(url=f'/reactions'))]
