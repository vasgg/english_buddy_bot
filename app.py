import logging
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from bot.database.db import db
from bot.database.models.lesson import Lesson
from bot.database.models.slide import Slide
from bot.database.models.text import Text

app = FastAPI()
templates = Jinja2Templates(directory='src/API/templates')


@app.get('/', response_class=HTMLResponse)
async def read_root():
    html_content = Path('src/API/index.html').read_text()
    return HTMLResponse(content=html_content)


@app.get("/texts", response_class=HTMLResponse)
async def read_texts(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Text))
        data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="texts.html", context={'texts': data})


@app.get("/lessons")
async def show_lessons(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Lesson))
        data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="lessons.html", context={'lessons': data})


@app.get("/edit-lesson/{lesson_id}")
async def edit_lesson(lesson_id: int, request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Lesson).where(Lesson.id == lesson_id))
        data = result.scalars().first()
    if data is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return templates.TemplateResponse("lesson.html", {"request": request, "lesson": data})


@app.get("/slides/{lesson_id}/{slide_id}")
async def edit_slide(lesson_id: int, slide_id: int, request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Slide).where(Lesson.id == lesson_id, Slide.id == slide_id))
        data = result.scalars().first()
    if data is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    return templates.TemplateResponse("slide.html", {"request": request, "slide": data, "lesson_id": lesson_id})


@app.post("/save-texts")
async def save_texts(request: Request):
    try:
        async with db.session_factory.begin() as db_session:
            form_data = await request.form()
            for key, value in form_data.items():
                logging.info(f"Updating text for prompt: {key}")
                db_text = await db_session.execute(select(Text).where(Text.prompt == key))
                db_text = db_text.scalar_one_or_none()
                if db_text:
                    db_text.text = value
                else:
                    raise HTTPException(status_code=404, detail=f"Text with prompt '{key}' not found")
            await db_session.commit()
        return {"message": "Texts updated successfully"}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/update-lesson/{lesson_id}")
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
