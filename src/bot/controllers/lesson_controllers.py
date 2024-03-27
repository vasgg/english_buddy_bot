import logging

from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.slide import get_slide_by_id
from database.models.slide import Slide

logger = logging.Logger(__name__)


async def find_first_exam_slide_id(slide_ids: list[int], db_session: AsyncSession) -> int | None:
    for slide_id in slide_ids:
        slide: Slide = await get_slide_by_id(slide_id, db_session)
        if slide.is_exam_slide:
            return slide_id
    return None
