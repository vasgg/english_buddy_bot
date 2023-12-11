from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.slide import Slide


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
