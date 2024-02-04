import logging

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from bot.database.db import db
from bot.database.models.lesson import Lesson

lessons_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@lessons_router.get("/lessons")
async def show_lessons(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Lesson))
        data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="lessons.html", context={'lessons': data})


@lessons_router.get("/edit-lesson/{lesson_id}")
async def edit_lesson(lesson_id: int, request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Lesson).where(Lesson.id == lesson_id))
        data = result.scalars().first()
    if data is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return templates.TemplateResponse("lesson.html", {"request": request, "lesson": data})


@lessons_router.post("/edit-lesson/{lesson_id}")
async def update_lesson(
    lesson_id: int,
    first_slide_id: str = Form(...),
    exam_slide_id: str = Form(...),
    is_paid: bool = Form(...),
    total_slides: int = Form(...),
):
    try:
        async with db.session_factory.begin() as db_session:
            stmt = select(Lesson).where(Lesson.id == lesson_id)
            result = await db_session.execute(stmt)
            lesson = result.scalar_one_or_none()

            if not lesson:
                raise HTTPException(status_code=404, detail="Lesson not found")

            lesson.first_slide_id = first_slide_id
            lesson.exam_slide_id = exam_slide_id
            lesson.is_paid = is_paid
            lesson.total_slides = total_slides

            await db_session.commit()

            return {"message": "Lesson updated successfully"}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
