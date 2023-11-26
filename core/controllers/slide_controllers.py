
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Slide


async def get_slide(lesson_number: int, slide_number: int, session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.lesson_id == lesson_number, Slide.id == slide_number)
    result: Result = await session.execute(query)
    slide = result.scalar()
    return slide

