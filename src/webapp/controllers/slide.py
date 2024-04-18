import logging

from database.crud.slide import get_slide_by_id
from webapp.controllers.misc import get_slide_details, get_slide_emoji
from webapp.db import AsyncDBSession
from webapp.schemas.slide import SlidesTableSchema

logger = logging.getLogger()


async def get_all_slides_from_lesson_by_order_fastui(path: str, db_session: AsyncDBSession) -> list:
    slides_ids = [int(slideid) for slideid in path.split('.')]
    ordered_slides = []
    for index, slide_id in enumerate(slides_ids, start=1):
        slide = await get_slide_by_id(slide_id, db_session)
        slide_text = (
            slide.slide_type.value.replace('_', ' ').capitalize()
            if 'sticker' in slide.slide_type.value
            else slide.text
        )
        slide_data = {
            'id': slide.id,
            'lesson_id': slide.lesson_id,
            'slide_type': slide.slide_type,
            'index': index,
            'emoji': get_slide_emoji(slide.slide_type),
            'text': slide.picture if slide.slide_type.value == 'image' else slide_text,
            'details': get_slide_details(slide),
            'is_exam_slide': '🎓' if slide.is_exam_slide else ' ',
            'edit_button': '✏️',
            'up_button': '🔼',
            'down_button': '🔽',
            'plus_button': '➕',
            'minus_button': '➖',
        }
        validated_slide = SlidesTableSchema.model_validate(slide_data)
        ordered_slides.append(validated_slide)
    logger.info(f"Processed slides: {len(ordered_slides)}")
    return ordered_slides


async def get_all_slides_from_lesson_by_order(path: str, db_session: AsyncDBSession) -> list:
    slides_ids = [int(slide_id) for slide_id in path.split('.')]
    ordered_slides = []
    for slide_id in slides_ids:
        slide = await get_slide_by_id(slide_id, db_session)
        ordered_slides.append(slide)
    return ordered_slides
