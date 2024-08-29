import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi.exceptions import ResponseValidationError
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from database.crud.lesson import (
    get_active_lessons,
    get_lesson_by_id,
    get_lesson_by_index,
    update_lesson_status,
)
from database.crud.session import abort_in_progress_sessions_by_lesson
from database.models.lesson import Lesson
from enums import LessonStatus
from webapp.controllers.lesson import (
    get_active_lessons_fastui,
    get_editing_lessons_fastui,
    recompose_lesson_indexes,
)
from webapp.db import AsyncDBSession
from webapp.routers.components.buttons import back_button, create_lesson_button
from webapp.routers.components.components import get_common_content
from webapp.routers.components.tables import get_active_lesson_table, get_editing_lesson_table
from webapp.schemas.lesson import (
    EditLessonDataModel,
    NewLessonDataModel,
    get_lesson_data_model,
    get_new_lesson_data_model,
)

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('lessons router called')
    active_lessons = await get_active_lessons_fastui(db_session)
    editing_lessons = await get_editing_lessons_fastui(db_session)

    active_lessons_heading = [
        c.Heading(text='Активные уроки', level=4),
        c.Paragraph(text=''),
        get_active_lesson_table(active_lessons) if len(active_lessons) > 0 else c.Paragraph(text='Нет активных уроков'),
        c.Paragraph(text=''),
    ]
    editing_lessons_heading = [
        c.Heading(text='Уроки в режиме редактирования', level=4),
        c.Paragraph(text=''),
        get_editing_lesson_table(editing_lessons)
        if len(editing_lessons) > 0
        else c.Paragraph(text='Нет уроков в режиме редактирования'),
        c.Paragraph(text=''),
    ]

    return get_common_content(
        c.Paragraph(text=''),
        *active_lessons_heading,
        *editing_lessons_heading,
        create_lesson_button,
        title='Уроки',
    )


@router.get("/edit/{lesson_status}/{lesson_id}/", response_model=FastUI, response_model_exclude_none=True)
async def show_lesson(
    lesson_id: int, lesson_status: LessonStatus, db_session: AsyncDBSession, index: int | None = None
) -> list[AnyComponent]:
    lesson = await get_lesson_by_id(lesson_id, db_session)
    if lesson_status == LessonStatus.ACTIVE:
        submit_url = f'/api/lessons/edit/{lesson_status}/{lesson_id}/?index={index}'
    else:
        submit_url = f'/api/lessons/edit/{lesson_status}/{lesson_id}/'
    form = c.ModelForm(model=get_lesson_data_model(lesson), submit_url=submit_url)
    return get_common_content(
        c.Paragraph(text=''),
        form,
        title=f'edit | lesson {lesson.index} | {lesson.title}',
    )


@router.post('/edit/{lesson_status}/{lesson_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_lesson_form(
    lesson_id: int,
    lesson_status: LessonStatus,
    db_session: AsyncDBSession,
    form: Annotated[EditLessonDataModel, fastui_form(EditLessonDataModel)],
    index: int | None = None,
):
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    lesson.title = form.title
    lesson.errors_threshold = form.errors_threshold if form.errors_threshold else None
    lesson.is_paid = bool(form.is_paid)
    if lesson_status == LessonStatus.ACTIVE and form.is_active is False:
        await update_lesson_status(lesson_id, LessonStatus.EDITING, db_session)
        await recompose_lesson_indexes(index, db_session)
        await abort_in_progress_sessions_by_lesson(lesson.id, db_session)
    elif lesson_status == LessonStatus.EDITING and form.is_active is True:
        lesson.index = len(await get_active_lessons(db_session)) + 1
        logger.info(f'index updated to {lesson.index}')
        lesson.is_active = LessonStatus.ACTIVE
    # noinspection PyTypeChecker
    logger.info(f'lesson {lesson.id} updated. data: {form.dict()}')
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]


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
            logger.info(f'lesson {lesson.id} updated to {lesson.index}, lesson_with_target_index '
                        f'{lesson_with_target_index.id} updated to {lesson_with_target_index.index}')
            lesson_with_target_index.index = index
    except ResponseValidationError:
        logger.exception('unexpected behavior')
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]


@router.get('/down_button/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def down_button(index: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed down_button with index {index}')
    lessons = await get_active_lessons(db_session)
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
            logger.info(f'lesson {lesson.id} updated to {lesson.index}, lesson_with_target_index '
                        f'{lesson_with_target_index.id} updated to {lesson_with_target_index.index}')
    except ResponseValidationError:
        logger.exception('unexpected behavior')
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]


@router.get('/add_lesson/', response_model=FastUI, response_model_exclude_none=True)
async def add_lesson() -> list[AnyComponent]:
    submit_url = '/api/lessons/new/'
    form = c.ModelForm(model=get_new_lesson_data_model(), submit_url=submit_url)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title='Создание урока',
    )


@router.get('/confirm_delete/{lesson_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_lesson_confirm(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    return get_common_content(
        c.Paragraph(text='Вы уверены, что хотите удалить урок?'),
        c.Div(
            components=[
                back_button,
                c.Link(
                    components=[c.Button(text='Удалить', named_style='warning')],
                    on_click=GoToEvent(url=f'/lessons/delete/{lesson.id}/'),
                    class_name='+ ms-2',
                ),
            ],
        ),
        title=f'Удаление урока {lesson.index} | {lesson.title}',
    )


@router.get('/delete/{lesson_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_lesson(
    lesson_id: int,
    db_session: AsyncDBSession,
):
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    indx = lesson.index if lesson.index else None
    await update_lesson_status(lesson_id, LessonStatus.DISABLED, db_session)
    if indx is not None:
        # noinspection PyTypeChecker
        await recompose_lesson_indexes(indx, db_session)
    await abort_in_progress_sessions_by_lesson(lesson_id, db_session)
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]


@router.post('/new/', response_model=FastUI, response_model_exclude_none=True)
async def create_new_lesson(
    db_session: AsyncDBSession,
    form: Annotated[NewLessonDataModel, fastui_form(NewLessonDataModel)],
):
    new_lesson = Lesson(
        title=form.title,
        errors_threshold=form.errors_threshold,
        is_paid=form.is_paid,
    )
    db_session.add(new_lesson)
    await db_session.flush()
    directory = Path(f"src/webapp/static/lessons_images/{new_lesson.id}")
    directory.mkdir(parents=True, exist_ok=True)
    return [c.FireEvent(event=GoToEvent(url='/lessons'))]
