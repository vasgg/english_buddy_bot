import logging
from typing import Annotated

from fastapi import APIRouter
from fastapi.exceptions import ResponseValidationError
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from bot.controllers.lesson_controllers import get_lesson_by_id, get_lesson_by_index, get_lessons
from controllers.lesson import get_lessons_fastui
from database.db import AsyncDBSession
from database.models.lesson import Lesson
from database.schemas.lesson import EditLessonDataModel, get_lesson_data_model
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get("", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('lessons router called')
    lessons = await get_lessons_fastui(db_session)
    return get_common_content(
        c.Paragraph(text=''),
        # c.Heading(text='Lessons', level=2),
        c.Table(
            data=lessons,
            columns=[
                DisplayLookup(
                    field='title',
                ),
                DisplayLookup(
                    field='is_paid',
                    table_width_percent=13,
                ),
                DisplayLookup(
                    field='first_slide_id',
                    table_width_percent=13,
                ),
                DisplayLookup(
                    field='exam_slide_id',
                    table_width_percent=13,
                ),
                DisplayLookup(
                    field='total_slides',
                    table_width_percent=13,
                ),
                DisplayLookup(
                    field='slides',
                    on_click=GoToEvent(url='/slides/lesson{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='edit_button',
                    on_click=GoToEvent(url='/lessons/edit/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='up_button', on_click=GoToEvent(url='/lessons/up_button/{index}/'), table_width_percent=3
                ),
                DisplayLookup(
                    field='down_button', on_click=GoToEvent(url='/lessons/down_button/{index}/'), table_width_percent=3
                ),
                DisplayLookup(field='plus_button', on_click=GoToEvent(url='/user/{id}/'), table_width_percent=3),
            ],
        ),
        title='Уроки',
    )


@app.get("/edit/{lesson_id}/", response_model=FastUI, response_model_exclude_none=True)
async def show_lesson(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    lesson = await get_lesson_by_id(lesson_id, db_session)
    submit_url = f'/api/lessons/edit/{lesson_id}/'
    form = c.ModelForm(model=get_lesson_data_model(lesson), submit_url=submit_url)
    return get_common_content(
        c.Paragraph(text=''),
        form,
        title=f'edit | lesson {lesson.index} | {lesson.title}',
    )


@app.get('/up_button/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def up_button(index: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed up_button with index {index}')
    try:
        if index == 1:
            pass
        else:
            lesson = await get_lesson_by_index(index, db_session)
            lesson_with_target_index = await get_lesson_by_index(index - 1, db_session)
            lesson.index = None
            lesson_with_target_index.index = None
            await db_session.flush()
            lesson.index = index - 1
            lesson_with_target_index.index = index
            await db_session.commit()
    except ResponseValidationError:
        pass
    return [c.FireEvent(event=GoToEvent(url=f'/lessons'))]


@app.get('/down_button/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def down_button(index: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed down_button with index {index}')
    lessons = await get_lessons(db_session)
    try:
        if index == len(lessons):
            pass
        else:
            lesson = await get_lesson_by_index(index, db_session)
            lesson_with_target_index = await get_lesson_by_index(index + 1, db_session)
            lesson.index = None
            lesson_with_target_index.index = None
            await db_session.flush()
            lesson.index = index + 1
            lesson_with_target_index.index = index
            await db_session.commit()
    except ResponseValidationError:
        pass
    return [c.FireEvent(event=GoToEvent(url=f'/lessons'))]


@app.post('/edit/{lesson_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_lesson_form(
    lesson_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditLessonDataModel, fastui_form(EditLessonDataModel)],
):
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(lesson, field, form_value)
    await db_session.commit()
    logger.info(f'lesson {lesson.id} updated. data: {form.dict()}')
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]
