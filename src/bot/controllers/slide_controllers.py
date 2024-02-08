import logging
import os

from fastapi import File
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models.lesson import Lesson
from bot.database.models.slide import Slide
from bot.resources.enums import SlideType


async def get_all_base_questions_id_in_lesson(
    lesson_id: int, exam_slides_id: set[int], db_session: AsyncSession
) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.lesson_id == lesson_id, Slide.slide_type.in_(all_questions_slide_types), ~Slide.id.in_(exam_slides_id)
    )
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()} if result else {}


async def get_slide_by_id(slide_id: int, db_session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.id == slide_id)
    result = await db_session.execute(query)
    slide = result.scalar()
    return slide


async def get_slide_by_position(position: int, db_session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.next_slide == position)
    result = await db_session.execute(query)
    slide = result.scalar()
    return slide


async def get_steps_to_current_slide(first_slide_id: int, target_slide_id: int, db_session: AsyncSession) -> int:
    current_slide_id = first_slide_id
    steps = 0

    while current_slide_id is not None:
        if current_slide_id == target_slide_id:
            return steps
        result = await db_session.execute(select(Slide).filter(Slide.id == current_slide_id))
        current_slide = result.scalar_one()
        current_slide_id = current_slide.next_slide
        steps += 1


async def set_new_slide_image(slide_id: int, image_name: str, db_session: AsyncSession):
    stmt = select(Slide).filter(Slide.id == slide_id)
    result = await db_session.execute(stmt)
    slide = result.scalar_one()
    slide.picture = image_name
    await db_session.commit()


async def update_slides_order(slide_id: int, next_slide: int | None, db_session: AsyncSession):
    await db_session.execute(update(Slide).where(Slide.id == slide_id).values(next_slide=next_slide))


async def reset_next_slide_for_all_slides_in_lesson(lesson_id: int, db_session):
    await db_session.execute(update(Slide).where(Slide.lesson_id == lesson_id).values(next_slide=None))


async def get_all_slides_from_lesson_by_order(lesson_id, db_session):
    slides_query = await db_session.execute(select(Slide).where(Slide.lesson_id == lesson_id))
    slides = slides_query.scalars().all()
    slides_dict = {slide.id: slide for slide in slides}
    ordered_slides = []
    first_slide_query = await db_session.execute(select(Lesson.first_slide_id).where(Lesson.id == lesson_id))
    current_slide = first_slide_query.scalar()
    while current_slide:
        current_slide = slides_dict.get(current_slide)
        if current_slide:
            ordered_slides.append(current_slide)
            current_slide = current_slide.next_slide
        else:
            break
    return ordered_slides


def allowed_image_file_to_upload(file: File) -> bool:
    check = file.content_type in settings.allowed_MIME_types_to_upload
    logging.info(f"File {file.filename} is allowed to upload: {check}")
    return check


def get_image_files_list(lesson_id: int) -> list[str]:
    directory = f'src/webapp/static/images/lesson_{lesson_id}'
    allowed_image_formats = ['png', 'jpg', 'jpeg', 'gif', 'heic', 'tiff', 'webp']
    files = []
    for filename in os.listdir(directory):
        if filename.rsplit('.', 1)[1].lower() in allowed_image_formats:
            files.append(filename)
    return files
