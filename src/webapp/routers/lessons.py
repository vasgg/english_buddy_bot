import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select

from bot.database.db import db
from bot.database.models.lesson import Lesson
from webapp.shemas import LessonData

lessons_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@lessons_router.get("/lessons")
async def show_lessons(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Lesson))
        data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="lessons.html", context={'lessons': data})


@lessons_router.get("/lesson/{lesson_id}")
async def show_edit_lesson_page(lesson_id: int, request: Request):
    async with db.session_factory.begin() as db_session:
        data = await db_session.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = data.scalars().first()
        lessons_count = await db_session.scalar(select(func.count()).select_from(Lesson))

    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return templates.TemplateResponse(
        "lesson.html", {"request": request, "lesson": lesson, "lessons_count": lessons_count}
    )


@lessons_router.post("/lesson/{lesson_id}")
async def update_lesson(lesson_data: LessonData):
    try:
        async with db.session_factory.begin() as db_session:
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
