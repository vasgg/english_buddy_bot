import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select

from bot.controllers.lesson_controllers import reset_index_for_all_lessons, update_lesson_index
from bot.database.db import db
from bot.database.models.lesson import Lesson
from webapp.shemas import LessonData, LessonOrderUpdateRequest

lessons_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@lessons_router.get("/lessons")
async def show_lessons(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Lesson).group_by(Lesson.index))
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


@lessons_router.delete("/lesson/{lesson_id}")
async def delete_lesson(lesson_id: int):
    async with db.session_factory.begin() as transaction:
        ...


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


@lessons_router.post("/save-lessons-order")
async def save_lessons_order(order_data: LessonOrderUpdateRequest):
    logging.info(f'{order_data}')
    async with db.session_factory.begin() as transaction:
        try:
            await reset_index_for_all_lessons(db_session=transaction)
            logging.info("all index fields are reset")

            for lessons in order_data.lessons:
                await update_lesson_index(
                    lesson_id=lessons.lesson_id, index=lessons.lesson_index, db_session=transaction
                )
            await transaction.commit()
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            await transaction.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Lessons order updated successfully"}
