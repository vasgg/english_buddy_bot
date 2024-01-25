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
