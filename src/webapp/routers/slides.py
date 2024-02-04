import logging
import shutil
import traceback
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, select

from bot.controllers.lesson_controllers import update_lesson_exam_slide, update_lesson_first_slide
from bot.controllers.slide_controllers import (
    allowed_image_file_to_upload,
    get_all_slides_from_lesson_by_order,
    get_image_files_list,
    get_slide_by_id,
    reset_next_slide_for_all_slides_in_lesson,
    update_slides_order,
)
from bot.database.db import db
from bot.database.models.lesson import Lesson
from bot.database.models.slide import Slide
from bot.resources.enums import KeyboardType, SlideType
from webapp.shemas import CreateNewSlideBellow, SlideOrderUpdateRequest

slides_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@slides_router.get("/slides/{slide_id}")
async def edit_slide(slide_id: int, request: Request):
    async with db.session_factory.begin() as db_session:
        slide = await db_session.execute(select(Slide).where(Slide.id == slide_id))
        slide = slide.scalars().first()
        previous_slide = await db_session.execute(select(Slide).where(Slide.next_slide == slide.id))
        previous_slide = previous_slide.scalars().first()
        lesson = await db_session.execute(select(Lesson).where(Lesson.id == slide.lesson_id))
        lesson = lesson.scalars().first()
        files = get_image_files_list(lesson.id)
    if slide is None or lesson is None:
        raise HTTPException(status_code=404, detail="Slide not found")
    return templates.TemplateResponse(
        'slide.html',
        {'request': request, 'lesson': lesson, 'slide': slide, 'previous_slide': previous_slide, 'files': files},
    )


@slides_router.delete("/slides/{slide_id}")
async def delete_slide(slide_id: int):
    async with db.session_factory.begin() as transaction:
        try:
            slide_query = await transaction.execute(select(Slide).filter(Slide.id == slide_id))
            slide = slide_query.scalar_one_or_none()
            if slide is None:
                logging.error(f"Slide with id {slide_id} not found.")
                raise HTTPException(status_code=404, detail=f"Slide with id {slide_id} not found")
            lesson_query = await transaction.execute(select(Lesson).where(Lesson.id == slide.lesson_id))
            lesson = lesson_query.scalar_one_or_none()
            if lesson is None:
                logging.error(f"lesson with id {slide.lesson_id} not found.")
                raise HTTPException(status_code=404, detail=f"lesson with id {slide.lesson_id} not found.")
            temp = slide.next_slide
            if lesson.first_slide_id == slide.id:
                await update_lesson_first_slide(lesson_id=lesson.id, first_slide_id=temp, db_session=transaction)
            elif lesson.exam_slide_id == slide.id:
                await update_lesson_exam_slide(lesson_id=lesson.id, exam_slide_id=temp, db_session=transaction)
            await transaction.execute(delete(Slide).filter(Slide.id == slide_id))
            previous_slide_query = await transaction.execute(select(Slide).where(Slide.next_slide == slide_id))
            previous_slide = previous_slide_query.scalar_one_or_none()
            if previous_slide is not None:
                previous_slide.next_slide = temp
                await transaction.commit()
                logging.info(f"Slide {slide_id} deleted successfully.")
            else:
                logging.info(f"No previous slide found for slide id {slide_id}.")
                await transaction.commit()
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
    new_picture: Optional[UploadFile] = File(None),
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
                    slide.next_slide_id = next_slide
                    slide.text = text
                    slide.delay = delay
                    slide.keyboard_type = keyboard_type
                case SlideType.IMAGE:
                    slide.next_slide_id = next_slide
                    slide.picture = picture
                    slide.delay = delay
                    slide.keyboard_type = keyboard_type
                case SlideType.PIN_DICT:
                    slide.next_slide_id = next_slide
                    slide.text = text
                case SlideType.QUIZ_OPTIONS:
                    slide.next_slide_id = next_slide
                    slide.text = text
                    slide.right_answers = right_answers
                    slide.keyboard = keyboard
                    slide.is_exam_slide = False if is_exam_slide is None else is_exam_slide
                case SlideType.QUIZ_INPUT_WORD:
                    slide.next_slide_id = next_slide
                    slide.text = text
                    slide.right_answers = right_answers
                    slide.is_exam_slide = False if is_exam_slide is None else is_exam_slide
                case SlideType.QUIZ_INPUT_PHRASE:
                    slide.next_slide_id = next_slide
                    slide.text = text
                    slide.right_answers = right_answers
                    slide.almost_right_answers = almost_right_answers
                    slide.almost_right_answer_reply = almost_right_answer_reply
                    slide.is_exam_slide = False if is_exam_slide is None else is_exam_slide
                case SlideType.FINAL_SLIDE:
                    slide.next_slide_id = next_slide
                    slide.text = text
            if new_picture and new_picture.filename:
                logging.info(f"New picture: {new_picture.filename}")
                file_path = f"src/webapp/static/images/lesson{slide.lesson_id}/{new_picture.filename}"
                if allowed_image_file_to_upload(new_picture.filename):
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(new_picture.file, buffer)
                    slide.picture = new_picture.filename
                else:
                    return {'message': 'Invalid file type'}
            await db_session.commit()
        return {'message': 'Slide updated successfully'}
    except Exception as e:
        traceback.print_exc()
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


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
async def add_slide(data: CreateNewSlideBellow):
    logging.info('[slide_type]: ', data.slide_type)
    logging.info('[slide_id]: ', data.slide_id)
    async with db.session_factory.begin() as transaction:
        try:
            slide = await get_slide_by_id(data.slide_id, transaction)
            temp = slide.next_slide
            slide.next_slide = None
            await transaction.flush()
            new_slide = Slide(
                lesson_id=slide.lesson_id,
                next_slide=temp,
                slide_type=data.slide_type,
                text=f"New {data.slide_type} slide template",
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


@slides_router.post("/save-slides-order")
async def save_slides_order(order_data: SlideOrderUpdateRequest):
    logging.info(f'[order_data]: {order_data}')
    async with db.session_factory.begin() as transaction:
        try:
            await reset_next_slide_for_all_slides_in_lesson(order_data.slides[0].lesson_id, transaction)
            logging.info("all next_slide fields reset")
            for slide in order_data.slides:
                await update_slides_order(slide.slide_id, slide.next_slide_id, transaction)
            logging.info("all next_slide fields updated")
            await update_lesson_first_slide(order_data.slides[0].lesson_id, order_data.slides[0].slide_id, transaction)
            logging.info(f"first_slide_id updated: {order_data.slides[0].slide_id}")
            await transaction.commit()
        except Exception as e:
            await transaction.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Order updated successfully"}
