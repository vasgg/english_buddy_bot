import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from webapp.schemas import CreateNewLessonRequest, LessonData, LessonOrderUpdateRequest

from database.db import AsyncDBSession
from database.models.lesson import Lesson

lessons_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@lessons_router.get("/lessons")
async def show_lessons(request: Request, db_session: AsyncDBSession):
    result = await db_session.execute(select(Lesson).group_by(Lesson.index))
    data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="lessons.html", context={'lessons': data})


@lessons_router.get("/lesson/{lesson_id}")
async def show_edit_lesson_page(lesson_id: int, request: Request, db_session: AsyncDBSession):
    data = await db_session.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = data.scalars().first()
    lessons_count = await db_session.scalar(select(func.count()).select_from(Lesson))
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return templates.TemplateResponse(
        "lesson.html", {"request": request, "lesson": lesson, "lessons_count": lessons_count}
    )


@lessons_router.post("/lesson/{lesson_id}")
async def update_lesson(lesson_data: LessonData, db_session: AsyncDBSession):
    try:
        stmt = select(Lesson).where(Lesson.id == lesson_data.id)
        result = await db_session.execute(stmt)
        lesson = result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        lesson.title = lesson_data.title
        lesson.first_slide_id = lesson_data.first_slide_id
        if not lesson_data.exam_slide_id:
            lesson.exam_slide_id = None
        lesson.is_paid = lesson_data.is_paid
        lesson.total_slides = lesson_data.total_slides

        await db_session.commit()

        return {"message": f'Lesson "{lesson_data.title}" updated successfully'}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@lessons_router.post("/save-lessons-order")
async def save_lessons_order(order_data: LessonOrderUpdateRequest, db_session: AsyncDBSession):
    logging.info(f'{order_data}')
    from bot.controllers.lesson_controllers import reset_index_for_all_lessons, update_lesson_index

    await reset_index_for_all_lessons(db_session=db_session)
    logging.info("all index fields are reset")
    for lessons in order_data.lessons:
        await update_lesson_index(lesson_id=lessons.lesson_id, index=lessons.lesson_index, db_session=db_session)
    return {"message": "Lessons order updated successfully"}


@lessons_router.post('/add-lesson')
async def add_lesson(data: CreateNewLessonRequest, db_session: AsyncDBSession):
    from bot.controllers.lesson_controllers import get_lesson_by_id, get_lessons_with_greater_index

    parent_lesson = await get_lesson_by_id(data.lesson_id, db_session)
    new_lesson = Lesson(
        index=parent_lesson.index + 1,
        title='NEW LESSON TEMPLATE',
    )
    lessons = await get_lessons_with_greater_index(parent_lesson.index + 1, db_session)
    for lesson in lessons:
        lesson.index = lesson.index + 1
    db_session.add(new_lesson)
    await db_session.flush()
    directory = Path(f"src/webapp/static/images/lesson_{new_lesson.id}")
    directory.mkdir(parents=True, exist_ok=True)
    logging.info(f"Added new lesson: {new_lesson.id}")
    await db_session.commit()
    return {
        "message": f"Lesson added successfully. Lesson ID: {new_lesson.id}",
        "redirectUrl": f"/lesson/{new_lesson.id}",
    }
