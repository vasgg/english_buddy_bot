import logging

from fastapi import APIRouter
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from controllers.text import get_texts_table_content
from database.db import AsyncDBSession
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get("/texts", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page(db_session: AsyncDBSession) -> list[AnyComponent]:
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
                    on_click=GoToEvent(url='/reactions/modal-prompt/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='minus_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/modal-prompt/{id}'),
                    table_width_percent=3,
                ),
            ],
            # class_name='text-decoration-none',
        ),
        c.Paragraph(text=''),
        title='Тексты',
    )
