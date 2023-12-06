from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Lesson, Slide
from core.resources.enums import SlideType


async def get_slide_by_id(lesson_id: int, slide_id: int, session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.lesson_id == lesson_id, Slide.id == slide_id)
    result = await session.execute(query)
    slide = result.scalar()
    return slide


async def get_slide_by_position(lesson_id: int, position: int, session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.lesson_id == lesson_id, Slide.next_slide == position)
    result = await session.execute(query)
    slide = result.scalar()
    return slide


async def count_slides_by_type(session: AsyncSession, slide_types: list[SlideType]) -> int:
    query = select(func.count()).select_from(Slide).where(Slide.slide_type.in_(slide_types))
    result = await session.execute(query)
    return result.scalar_one()


async def set_progress_position(lesson_id: int, position: int, session: AsyncSession) -> None:
    ...
