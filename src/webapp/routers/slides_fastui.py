import logging

from fastapi import APIRouter
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup, DisplayMode
from fastui.events import GoToEvent

from controllers.slide import get_all_slides_from_lesson_by_order_fastui
from database.db import AsyncDBSession
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get("/slides/lesson{lesson_id}", response_model=FastUI, response_model_exclude_none=True)
async def slides_page(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    slides = await get_all_slides_from_lesson_by_order_fastui(lesson_id, db_session)
    return get_common_content(
        c.Paragraph(text=''),
        # c.Heading(text='Lesson 1', level=2),
        # c.Div(
        #     components=[
        #         c.Button(text='◀︎', named_style='secondary', class_name='+ ms-2'),
        #         c.Button(text='▶︎', named_style='warning', on_click=PageEvent(name='static-modal')),
        #     ]
        # ),
        c.Table(
            data=slides,
            columns=[
                DisplayLookup(
                    field='index',
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='emoji',
                    table_width_percent=3,
                ),
                DisplayLookup(field='text', mode=DisplayMode.plain),
                DisplayLookup(field='details', table_width_percent=20),
                DisplayLookup(field='is_exam_slide', table_width_percent=3),
                DisplayLookup(
                    field='edit_button',
                    mode=DisplayMode.plain,
                    on_click=GoToEvent(url='/slides/edit/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='up_button', on_click=GoToEvent(url='/slides/up_button/{id}/'), table_width_percent=3
                ),
                DisplayLookup(
                    field='down_button', on_click=GoToEvent(url='/slides/down_button/{id}/'), table_width_percent=3
                ),
                DisplayLookup(field='plus_button', table_width_percent=3),
                DisplayLookup(field='minus_button', table_width_percent=3),
            ],
        ),
        title='Слайды',
    )
