import logging
from pathlib import Path
import shutil
import traceback

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
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
from bot.resources.enums import SlideType
from webapp.schemas import CreateNewSlideRequest, SlideData, SlideOrderUpdateRequest

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
    return {"message": f"Slide {slide_id} deleted successfully"}


@slides_router.post("/slides/{slide_id}")
async def update_slide(slide_data: SlideData):
    try:
        async with db.session_factory.begin() as db_session:
            stmt = select(Slide).where(Slide.id == slide_data.slide_id)
            result = await db_session.execute(stmt)
            slide = result.scalar_one_or_none()
            if not slide:
                raise HTTPException(status_code=404, detail="Slide not found")

            match slide.slide_type:
                case SlideType.TEXT:
                    slide.next_slide_id = slide_data.next_slide
                    slide.text = slide_data.text
                    slide.delay = slide_data.delay
                    slide.keyboard_type = slide_data.keyboard_type
                case SlideType.IMAGE:
                    slide.next_slide_id = slide_data.next_slide
                    slide.picture = slide_data.picture
                    slide.delay = slide_data.delay
                    if slide_data.keyboard_type is not None:
                        slide.keyboard_type = slide_data.keyboard_type
                case SlideType.PIN_DICT:
                    slide.next_slide_id = slide_data.next_slide
                    slide.text = slide_data.text
                case SlideType.QUIZ_OPTIONS:
                    slide.next_slide_id = slide_data.next_slide
                    slide.text = slide_data.text
                    slide.right_answers = slide_data.right_answers
                    slide.keyboard = slide_data.keyboard
                    slide.is_exam_slide = False if slide_data.is_exam_slide is None else slide_data.is_exam_slide
                case SlideType.QUIZ_INPUT_WORD:
                    slide.next_slide_id = slide_data.next_slide
                    slide.text = slide_data.text
                    slide.right_answers = slide_data.right_answers
                    slide.is_exam_slide = False if slide_data.is_exam_slide is None else slide_data.is_exam_slide
                case SlideType.QUIZ_INPUT_PHRASE:
                    slide.next_slide_id = slide_data.next_slide
                    slide.text = slide_data.text
                    slide.right_answers = slide_data.right_answers
                    slide.almost_right_answers = slide_data.almost_right_answers
                    slide.almost_right_answer_reply = slide_data.almost_right_answer_reply
                    slide.is_exam_slide = False if slide_data.is_exam_slide is None else slide_data.is_exam_slide
                case SlideType.FINAL_SLIDE:
                    slide.next_slide_id = slide_data.next_slide
                    slide.text = slide_data.text
            await db_session.commit()
        return {'message': f'Slide updated successfully. Slide ID: {slide.id}'}
    except Exception as e:
        traceback.print_exc()
        logging.error(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@slides_router.post("/slides/{slide_id}/upload_picture")
async def upload_new_slide_picture(slide_id: int, new_picture: UploadFile | None = File(None)):
    async with db.session_factory.begin() as db_session:
        data = await db_session.execute(select(Slide).where(Slide.id == slide_id))
        slide = data.scalar_one_or_none()
        logging.info(f"New picture: {new_picture.filename}")
        directory = Path(f"src/webapp/static/images/lesson_{slide.lesson_id}")
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / new_picture.filename
        if allowed_image_file_to_upload(new_picture):
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(new_picture.file, buffer)
            slide.picture = new_picture.filename
        else:
            return {'message': f'Unsupported file type: {new_picture.content_type}'}
        await db_session.commit()
        return {'message': f'Slide{slide.id} updated successfully'}


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
async def add_slide(data: CreateNewSlideRequest):
    async with db.session_factory.begin() as transaction:
        try:
            if data.slide_id is None:
                slide = Slide(
                    lesson_id=data.lesson_id,
                    slide_type=data.slide_type,
                    text=f"New {data.slide_type} slide template",
                )
                transaction.add(slide)
                await transaction.flush()
                await update_lesson_first_slide(
                    lesson_id=data.lesson_id, first_slide_id=slide.id, db_session=transaction
                )
                await transaction.commit()
                return {
                    "message": f"Slide added successfully. Slide ID: {slide.id}",
                    "redirectUrl": f"/slides/{slide.id}",
                }
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
            slide.next_slide = new_slide.id
            await transaction.commit()
        except Exception as e:
            await transaction.rollback()
            logging.error(f"An error occurred during adding new slide: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"Slide added successfully. Slide ID: {new_slide.id}", "redirectUrl": f"/slides/{new_slide.id}"}


@slides_router.post("/save-slides-order")
async def save_slides_order(order_data: SlideOrderUpdateRequest):
    logging.info(f'[order_data]: {order_data}')
    async with db.session_factory.begin() as transaction:
        try:
            await reset_next_slide_for_all_slides_in_lesson(order_data.slides[0].lesson_id, transaction)
            logging.info("all next_slide fields are reset")
            for slide in order_data.slides:
                await update_slides_order(slide.slide_id, slide.next_slide_id, transaction)
            logging.info("all next_slide fields updated")
            await update_lesson_first_slide(order_data.slides[0].lesson_id, order_data.slides[0].slide_id, transaction)
            logging.info(f"first_slide_id updated: {order_data.slides[0].slide_id}")
            await transaction.commit()
        except Exception as e:
            await transaction.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Slides order updated successfully"}
