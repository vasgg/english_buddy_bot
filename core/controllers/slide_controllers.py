
from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Lesson, Slide, SlideOrder
from core.resources.enums import SlideType


async def get_slide(lesson_number: int, slide_number: int, session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.lesson_id == lesson_number, Slide.id == slide_number)
    result: Result = await session.execute(query)
    slide = result.scalar()
    return slide


async def get_slide_by_slide_index(lesson_number: int, slide_index: int, session: AsyncSession) -> Slide:
    subquery = select(SlideOrder.slide_id).where(
        SlideOrder.lesson_id == lesson_number,
        SlideOrder.slide_index == slide_index
    )
    query = select(Slide).filter(Slide.id.in_(subquery))
    result = await session.execute(query)
    slide = result.scalars().first()
    return slide


async def count_slides_by_type(session: AsyncSession, slide_types: list[SlideType]) -> int:
    query = select(func.count()).select_from(Slide).where(Slide.slide_type.in_(slide_types))
    result = await session.execute(query)
    return result.scalar_one()


async def increment_lesson_slides_amount(lesson_id: int, slides_amount: int, session: AsyncSession) -> int:
    query = update(Lesson).filter(Lesson.id == lesson_id).values(slides_amount=slides_amount + 1)
    await session.execute(query)
    return slides_amount + 1
