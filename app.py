import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from bot.database.db import db
from bot.database.models.answer import Answer
from bot.database.models.lesson import Lesson
from bot.database.models.slide import Slide
from bot.database.models.text import Text
from bot.resources.enums import KeyboardType, SlideType

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/API/static"), name="static")
templates = Jinja2Templates(directory='src/API/templates')


@app.get('/', response_class=HTMLResponse)
async def read_root():
    html_content = Path('src/API/templates/index.html').read_text()
    return HTMLResponse(content=html_content)


@app.get("/texts", response_class=HTMLResponse)
async def read_texts(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Text))
        data = result.scalars().all()
    return templates.TemplateResponse(request=request, name="texts.html", context={'texts': data})


@app.post("/texts")
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


@app.get("/reactions", response_class=HTMLResponse)
async def read_answers(request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Answer))
        data = result.scalars().all()
    right = [reaction for reaction in data if reaction.answer_type.value == 'right']
    wrong = [reaction for reaction in data if reaction.answer_type.value == 'wrong']
    return templates.TemplateResponse(request=request, name="reactions.html", context={'right': right, 'wrong': wrong})


@app.post("/reactions")
async def write_answers(request: Request):
    try:
        async with db.session_factory.begin() as db_session:
            form_data = await request.form()
            for id_, value in form_data.items():
                logging.info(f"Updating reaction for id: {id_}")
                db_reaction = await db_session.execute(select(Answer).where(Answer.id == id_))
                db_reaction = db_reaction.scalar_one_or_none()
                if db_reaction:
                    db_reaction.text = value
                else:
                    raise HTTPException(status_code=404, detail=f"Reaction with prompt '{id_}' not found")
            await db_session.commit()
        return {"message": "Reactions updated successfully"}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


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


@app.get("/slides/{slide_id}")
async def edit_slide(slide_id: int, request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Slide).where(Slide.id == slide_id))
        data = result.scalars().first()
    if data is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    return templates.TemplateResponse("slide.html", {"request": request, "slide": data})


@app.post("/slides/{slide_id}")
async def update_slide(
    slide_id: int,
    next_slide: int = Form(...),
    text: Optional[str] = Form(None),
    delay: Optional[int] = Form(None),
    keyboard_type: Optional[KeyboardType] = Form(None),
    keyboard: Optional[str] = Form(None),
    picture: Optional[str] = Form(None),
    right_answers: Optional[str] = Form(None),
    almost_right_answers: Optional[str] = Form(None),
    almost_right_answer_reply: Optional[str] = Form(None),
    is_exam_slide: Optional[bool] = Form(None),
):
    try:
        async with db.session_factory.begin() as db_session:
            stmt = select(Slide).where(Slide.id == slide_id)
            result = await db_session.execute(stmt)
            slide = result.scalar_one_or_none()

            if not slide:
                raise HTTPException(status_code=404, detail="Slide not found")

            match slide.slide_type:
                case SlideType.TEXT:
                    slide.next_slide = next_slide
                    slide.text = text
                    slide.delay = delay
                    slide.keyboard_type = keyboard_type
                case SlideType.IMAGE:
                    slide.next_slide = next_slide
                    slide.image = picture
                    slide.delay = delay
                    slide.keyboard_type = keyboard_type
                case SlideType.PIN_DICT:
                    slide.next_slide = next_slide
                    slide.text = text
                case SlideType.QUIZ_OPTIONS:
                    slide.next_slide = next_slide
                    slide.text = text
                    slide.right_answers = right_answers
                    slide.keyboard = keyboard
                    slide.is_exam_slide = False if is_exam_slide is None else is_exam_slide
                case SlideType.QUIZ_INPUT_WORD:
                    slide.next_slide = next_slide
                    slide.text = text
                    slide.right_answers = right_answers
                    slide.is_exam_slide = False if is_exam_slide is None else is_exam_slide
                case SlideType.QUIZ_INPUT_PHRASE:
                    slide.next_slide = next_slide
                    slide.text = text
                    slide.right_answers = right_answers
                    slide.almost_right_answers = almost_right_answers
                    slide.almost_right_answer_reply = almost_right_answer_reply
                    slide.is_exam_slide = False if is_exam_slide is None else is_exam_slide
                case SlideType.FINAL_SLIDE:
                    slide.next_slide = next_slide
                    slide.text = text

            await db_session.commit()

            return {"message": "Slide updated successfully"}
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
