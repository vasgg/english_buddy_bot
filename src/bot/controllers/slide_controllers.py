from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def get_slide_by_id(lesson_id: int, slide_id: int, db_session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.lesson_id == lesson_id, Slide.id == slide_id)
    result = await db_session.execute(query)
    slide = result.scalar()
    return slide


async def get_slide_by_position(lesson_id: int, position: int, db_session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.lesson_id == lesson_id, Slide.next_slide == position)
    result = await db_session.execute(query)
    slide = result.scalar()
    return slide


async def set_progress_position(lesson_id: int, position: int, db_session: AsyncSession) -> None:
    ...
