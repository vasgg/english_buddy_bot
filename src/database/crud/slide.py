from database.models.slide import Slide
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_slide_by_id(slide_id: int, db_session: AsyncSession) -> Slide:
    query = select(Slide).filter(Slide.id == slide_id)
    result = await db_session.execute(query)
    slide = result.scalar()
    return slide


async def find_first_exam_slide_id(slide_ids: list[int], db_session: AsyncSession) -> int | None:
    for slide_id in slide_ids:
        slide: Slide = await get_slide_by_id(slide_id, db_session)
        if slide.is_exam_slide:
            return slide_id
    return None
