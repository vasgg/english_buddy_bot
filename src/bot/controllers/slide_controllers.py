import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.database.models.slide import Slide
from src.bot.resources.enums import SlideType


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


async def reset_next_slide_for_all_slides(lesson_id: int, db_session):
    await db_session.execute(update(Slide).where(Slide.lesson_id == lesson_id).values(next_slide=None))


async def get_all_slides_from_lesson_by_order(lesson_id, db_session):
    result = await db_session.execute(select(Slide).where(Slide.lesson_id == lesson_id).group_by(Slide.next_slide))
    slides = result.scalars().all()
    for slide in slides:
        logging.info(slide.id, slide.next_slide)
    sorted_slides = slides[1:] + [slides[0]]
    return sorted_slides
