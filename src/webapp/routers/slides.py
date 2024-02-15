import io
import logging
from pathlib import Path

from PIL import Image
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, select

from bot.controllers.slide_controllers import add_new_slide
from bot.resources.enums import KeyboardType, SlideType
from database.db import AsyncDBSession
from database.models.lesson import Lesson
from database.models.slide import Slide
from webapp.schemas import CreateNewSlideRequest, SlideData, SlideOrderUpdateRequest

slides_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')
logger = logging.getLogger(__name__)


@slides_router.get("/slides/{slide_id}")
async def edit_slide(slide_id: int, request: Request, db_session: AsyncDBSession):
    from bot.controllers.slide_controllers import get_image_files_list

    slide = await db_session.execute(select(Slide).where(Slide.id == slide_id))
    slide = slide.scalars().first()
    previous_slide = await db_session.execute(select(Slide).where(Slide.next_slide == slide.id))
    previous_slide = previous_slide.scalars().first()
    lesson = await db_session.execute(select(Lesson).where(Lesson.id == slide.lesson_id))
    lesson = lesson.scalars().first()
    files = get_image_files_list(lesson.id)
    if slide is None or lesson is None:
        logger.error(f"Slide with id {slide_id} not found.")
        raise HTTPException(status_code=404, detail="Slide not found")
    return templates.TemplateResponse(
        'slide.html',
        {'request': request, 'lesson': lesson, 'slide': slide, 'previous_slide': previous_slide, 'files': files},
    )


@slides_router.delete("/slides/{slide_id}")
async def delete_slide(slide_id: int, db_session: AsyncDBSession):
    from bot.controllers.lesson_controllers import update_lesson_exam_slide, update_lesson_first_slide

    slide_query = await db_session.execute(select(Slide).filter(Slide.id == slide_id))
    slide = slide_query.scalar_one_or_none()
    if slide is None:
        logging.error(f"Slide with id {slide_id} not found.")
        raise HTTPException(status_code=404, detail=f"Slide with id {slide_id} not found")
    lesson_query = await db_session.execute(select(Lesson).where(Lesson.id == slide.lesson_id))
    lesson = lesson_query.scalar_one_or_none()
    if lesson is None:
        logging.error(f"lesson with id {slide.lesson_id} not found.")
        raise HTTPException(status_code=404, detail=f"lesson with id {slide.lesson_id} not found.")
    temp = slide.next_slide
    if lesson.first_slide_id == slide.id:
        await update_lesson_first_slide(lesson_id=lesson.id, first_slide_id=temp, db_session=db_session)
    elif lesson.exam_slide_id == slide.id:
        await update_lesson_exam_slide(lesson_id=lesson.id, exam_slide_id=temp, db_session=db_session)
    await db_session.execute(delete(Slide).filter(Slide.id == slide_id))
    previous_slide_query = await db_session.execute(select(Slide).where(Slide.next_slide == slide_id))
    previous_slide = previous_slide_query.scalar_one_or_none()
    if previous_slide is not None:
        previous_slide.next_slide = temp
        logger.info(f"Slide {slide_id} deleted successfully.")
    else:
        logger.info(f"No previous slide found for slide id {slide_id}.")
    return {"message": f"Slide {slide_id} deleted successfully"}


@slides_router.post("/slides/{slide_id}")
async def update_slide(slide_data: SlideData, db_session: AsyncDBSession):
    stmt = select(Slide).where(Slide.id == slide_data.slide_id)
    result = await db_session.execute(stmt)
    slide = result.scalar_one_or_none()
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    if not slide.next_slide:
        slide.next_slide = None
    match slide.slide_type:
        case SlideType.TEXT:
            slide.next_slide_id = slide_data.next_slide
            slide.text = slide_data.text
            slide.delay = slide_data.delay
            slide.keyboard_type = KeyboardType.FURTHER if slide_data.further_button else None
        case SlideType.IMAGE:
            slide.next_slide_id = slide_data.next_slide
            slide.picture = slide_data.picture
            slide.delay = slide_data.delay
            slide.keyboard_type = KeyboardType.FURTHER if slide_data.further_button else None
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
    return {
        'message': f'Slide updated successfully. Slide ID: {slide.id}',
        'redirectUrl': f'/lesson_{slide.lesson_id}/slides',
    }


@slides_router.post("/slides/{slide_id}/upload_picture")
async def upload_new_slide_picture(
    slide_id: int, db_session: AsyncDBSession, new_picture: UploadFile | None = File(None)
):
    from bot.controllers.slide_controllers import allowed_image_file_to_upload

    data = await db_session.execute(select(Slide).where(Slide.id == slide_id))
    slide = data.scalar_one_or_none()
    logger.info(f"New picture: {new_picture.filename}")
    directory = Path(f"src/webapp/static/images/lesson_{slide.lesson_id}")
    directory.mkdir(parents=True, exist_ok=True)
    if not allowed_image_file_to_upload(new_picture):
        return {'message': f'Unsupported file type: {new_picture.content_type}'}
    image_data = await new_picture.read()
    image = Image.open(io.BytesIO(image_data))
    if image.width > 800:
        new_height = int((800 / image.width) * image.height)
        image = image.resize((800, new_height), Image.Resampling.LANCZOS)
    file_path = directory / new_picture.filename
    with open(file_path, "wb") as buffer:
        image_format = new_picture.content_type
        image.save(buffer, format=image_format.split("/")[1])
    slide.picture = new_picture.filename
    await db_session.commit()
    return {'message': f'Slide{slide.id} updated successfully'}


@slides_router.get("/lesson_{lesson_id}/slides", response_class=HTMLResponse)
async def get_slides(request: Request, lesson_id: int, db_session: AsyncDBSession):
    from bot.controllers.slide_controllers import get_all_slides_from_lesson_by_order

    result = await db_session.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalars().first()
    slides = await get_all_slides_from_lesson_by_order(lesson_id, db_session)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return templates.TemplateResponse("slides.html", {"request": request, "lesson": lesson, "slides": slides})


@slides_router.post("/add-slide")
async def add_slide(data: CreateNewSlideRequest, db_session: AsyncDBSession):
    from bot.controllers.lesson_controllers import update_lesson_first_slide
    from bot.controllers.slide_controllers import get_slide_by_id

    if data.slide_id is None:
        new_slide = add_new_slide(
            lesson_id=data.lesson_id,
            slide_type=data.slide_type,
        )
        db_session.add(new_slide)
        await db_session.flush()
        await update_lesson_first_slide(lesson_id=data.lesson_id, first_slide_id=new_slide.id, db_session=db_session)
        await db_session.commit()
        logger.info(f"Added new slide alone: {new_slide.id}")
        return {
            "message": f"Slide added successfully. Slide ID: {new_slide.id}",
            "redirectUrl": f"/slides/{new_slide.id}",
        }
    slide = await get_slide_by_id(data.slide_id, db_session)
    temp = slide.next_slide
    slide.next_slide = None
    await db_session.flush()
    new_slide = add_new_slide(lesson_id=data.lesson_id, slide_type=data.slide_type, slide_id=temp)
    db_session.add(new_slide)
    await db_session.flush()
    logger.info(f"Added new slide after slide: {new_slide.id}")
    slide.next_slide = new_slide.id
    return {"message": f"Slide added successfully. Slide ID: {new_slide.id}", "redirectUrl": f"/slides/{new_slide.id}"}


@slides_router.post("/save-slides-order")
async def save_slides_order(order_data: SlideOrderUpdateRequest, db_session: AsyncDBSession):
    from bot.controllers.lesson_controllers import update_lesson_first_slide
    from bot.controllers.slide_controllers import reset_next_slide_for_all_slides_in_lesson, update_slides_order

    logging.info(f'[order_data]: {order_data}')
    await reset_next_slide_for_all_slides_in_lesson(order_data.slides[0].lesson_id, db_session)
    logger.info("all next_slide fields are reset")
    for slide in order_data.slides:
        await update_slides_order(slide.slide_id, slide.next_slide_id, db_session)
    logger.info("all next_slide fields updated")
    await update_lesson_first_slide(order_data.slides[0].lesson_id, order_data.slides[0].slide_id, db_session)
    logger.info(f"first_slide_id updated: {order_data.slides[0].slide_id}")
    return {"message": "Slides order updated successfully"}
