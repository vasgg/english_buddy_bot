import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi.exceptions import ResponseValidationError
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent
from fastui.forms import fastui_form

from database.crud.lesson import get_lesson_by_id, get_lesson_by_index, get_lessons, get_lessons_with_greater_index
from database.db import AsyncDBSession
from database.models.lesson import Lesson
from database.schemas.lesson import (
    EditLessonDataModel,
    NewLessonDataModel,
    get_lesson_data_model,
    get_new_lesson_data_model,
)
from webapp.controllers.lesson import get_lessons_fastui
from webapp.routers.components import get_common_content

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('lessons router called')
    lessons = await get_lessons_fastui(db_session)
    return get_common_content(
        c.Paragraph(text=''),
        c.Table(
            data=lessons,
            columns=[
                DisplayLookup(
                    field='index',
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='title',
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
                    field='is_paid',
                    table_width_percent=3,
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
                DisplayLookup(
                    field='plus_button',
                    on_click=GoToEvent(url='/lessons/plus_button/{index}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='minus_button',
                    on_click=GoToEvent(url='/lessons/confirm_delete/{index}/'),
                    table_width_percent=3,
                ),
            ],
        ),
        title='Уроки',
    )


@router.get("/edit/{lesson_id}/", response_model=FastUI, response_model_exclude_none=True)
async def show_lesson(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    lesson = await get_lesson_by_id(lesson_id, db_session)
    submit_url = f'/api/lessons/edit/{lesson_id}/'
    form = c.ModelForm(model=get_lesson_data_model(lesson), submit_url=submit_url)
    return get_common_content(
        c.Paragraph(text=''),
        form,
        title=f'edit | lesson {lesson.index} | {lesson.title}',
    )


@router.get('/up_button/{index}/', response_model=FastUI, response_model_exclude_none=True)
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


@router.get('/down_button/{index}/', response_model=FastUI, response_model_exclude_none=True)
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


@router.post('/edit/{lesson_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_lesson_form(
    lesson_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditLessonDataModel, fastui_form(EditLessonDataModel)],
):
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    lesson.title = form.title
    lesson.exam_slide_id = form.exam_slide_id if form.exam_slide_id else None
    slides_ids[0] = 1 if form.is_paid else 0
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    logger.info(f'lesson {lesson.id} updated. data: {form.dict()}')
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]


@router.get('/plus_button/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def add_lesson(index: int) -> list[AnyComponent]:
    submit_url = f'/api/lessons/new/{index}/'
    form = c.ModelForm(model=get_new_lesson_data_model(), submit_url=submit_url)
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=''),
        form,
        title=f'Создание урока',
    )


@router.get('/confirm_delete/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_lesson_confirm(index: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    lesson: Lesson = await get_lesson_by_index(index, db_session)
    return get_common_content(
        c.Paragraph(text=f'Вы уверены, что хотите удалить урок?'),
        c.Div(
            components=[
                c.Link(
                    components=[c.Button(text='Назад', named_style='secondary')],
                    on_click=BackEvent(),
                    class_name='+ ms-2',
                ),
                c.Link(
                    components=[c.Button(text='Удалить', named_style='warning')],
                    on_click=GoToEvent(url=f'/lessons/delete/{index}/'),
                    class_name='+ ms-2',
                ),
            ]
        ),
        title=f'Удаление урока {lesson.index} | {lesson.title}',
    )


@router.get('/delete/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_slide(
    index: int,
    db_session: AsyncDBSession,
):
    lesson: Lesson = await get_lesson_by_index(index, db_session)
    lesson.is_active = False
    lesson.index = None
    await db_session.flush()
    lessons = await get_lessons_with_greater_index(index, db_session)
    for lesson in lessons:
        lesson.index -= 1
        await db_session.flush()
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lessons'))]


@router.post('/new/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def new_slide(
    index: int,
    db_session: AsyncDBSession,
    form: Annotated[NewLessonDataModel, fastui_form(NewLessonDataModel)],
):
    lessons = await get_lessons(db_session)
    for lesson in reversed(lessons[index:]):
        lesson.index += 1
        await db_session.flush()
    await db_session.commit()

    new_lesson: Lesson = Lesson(
        index=index + 1,
        title=form.title,
        path='1.' if form.is_paid else '0.',
    )
    db_session.add(new_lesson)
    await db_session.flush()
    directory = Path(f"src/webapp/static/lessons_images/{new_lesson.id}")
    directory.mkdir(parents=True, exist_ok=True)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]
