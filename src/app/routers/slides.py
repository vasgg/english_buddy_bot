import logging
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, select

from src.app.shemas import CreateNewSlideBellow, SlideOrderUpdateRequest
from src.bot.controllers.lesson_controllers import update_lesson_first_slide
from src.bot.controllers.slide_controllers import (
    get_all_slides_from_lesson_by_order,
    get_slide_by_id,
    reset_next_slide_for_all_slides,
    update_slides_order,
)
from src.bot.database.db import db
from src.bot.database.models.lesson import Lesson
from src.bot.database.models.slide import Slide
from src.bot.resources.enums import KeyboardType, SlideType

slides_router = APIRouter()
templates = Jinja2Templates(directory='src/app/templates')


@slides_router.get("/slides/{slide_id}")
async def edit_slide(slide_id: int, request: Request):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Slide).where(Slide.id == slide_id))
        data = result.scalars().first()
    if data is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    return templates.TemplateResponse("slide.html", {"request": request, "slide": data})


@slides_router.delete("/slides/{slide_id}")
async def delete_slide(slide_id: int):
    async with db.session_factory.begin() as transaction:
        try:
            query = await transaction.execute(select(Slide).filter(Slide.id == slide_id))
            slide = query.scalar_one_or_none()
            temp = slide.next_slide
            await transaction.execute(delete(Slide).filter(Slide.id == slide_id))
            previous_slide_query = await transaction.execute(select(Slide).where(Slide.next_slide == slide_id))
            previous_slide = previous_slide_query.scalar_one_or_none()
            previous_slide.next_slide = temp
            await transaction.commit()
            logging.info(f"Slide {slide_id} deleted successfully.")
        except Exception as e:
            await transaction.rollback()
            logging.error(f"An error occurred during slide deletion id{slide_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Slide deleted successfully"}


@slides_router.post("/slides/{slide_id}")
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


# @slides_router.post("/update-slide/{slide_id}")
# async def update_slide(slide: Slide, new_picture: UploadFile = File(None)):
#     if new_picture:
#         destination = f"static/images/lesson{slide.lesson_id}/{new_picture.filename}"
#         with open(destination, "wb") as buffer:
#             shutil.copyfileobj(new_picture.file, buffer)
#     async with db.session_factory.begin() as db_session:
#         await set_new_slide_image(slide.id, new_picture.filename, db_session)
#     return {"message": "Slide updated successfully"}


@slides_router.get("/lesson_{lesson_id}/slides", response_class=HTMLResponse)
async def get_slides(request: Request, lesson_id: int):
    async with db.session_factory.begin() as db_session:
        result = await db_session.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = result.scalars().first()
        slides = await get_all_slides_from_lesson_by_order(lesson_id, db_session)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return templates.TemplateResponse("slides.html", {"request": request, "lesson": lesson, "slides": slides})


@slides_router.post("/add-slide")
async def add_slide(slide_data: CreateNewSlideBellow):
    async with db.session_factory.begin() as transaction:
        try:
            slide = await get_slide_by_id(slide_data.slide_id, transaction)
            temp = slide.next_slide
            slide.next_slide = None
            await transaction.flush()
            new_slide = Slide(
                lesson_id=slide.lesson_id,
                next_slide=temp,
                slide_type=SlideType.TEXT,
                # TODO: вот тут можно придумать новый тип слайда
                # "щаблон". Потом у него разрешить редактирование всех полей, и подумать о
                # версионировании. Но непонятно, как игнорить шаблон на стороне телеграма, чтобы не показывать неготовые шаблоны
                text="New slide template",
            )
            transaction.add(new_slide)
            await transaction.flush()
            print(new_slide.id)
            slide.next_slide = new_slide.id
            await transaction.commit()
        except Exception as e:
            await transaction.rollback()
            logging.error(f"An error occurred during adding new slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"Slide added successfully. Slide ID: {new_slide.id}"}


@slides_router.post("/save-slide-order")
async def save_slide_order(order_data: SlideOrderUpdateRequest):
    logging.info('[order_data]: ', order_data)
    async with db.session_factory.begin() as transaction:
        try:
            await reset_next_slide_for_all_slides(order_data.slides[0].lesson_id, transaction)
            logging.info("all next_slide fields reset")
            for slide in order_data.slides:
                await update_slides_order(slide.slide_id, slide.next_slide, transaction)
            logging.info("all next_slide fields updated")
            await update_lesson_first_slide(order_data.slides[0].lesson_id, order_data.slides[0].slide_id, transaction)
            logging.info(f"first_slide_id updated: {order_data.slides[0].slide_id}")
            await transaction.commit()
        except Exception as e:
            await transaction.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Order updated successfully"}
