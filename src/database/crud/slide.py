from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.slide import Slide


async def get_slide_by_id(slide_id: int, db_session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.id == slide_id)
    result = await db_session.execute(query)
    slide = result.scalar()
    return slide
