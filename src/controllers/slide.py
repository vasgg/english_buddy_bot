import logging

from sqlalchemy import select

from controllers.misc import get_slide_details, get_slide_emoji
from database.models.lesson import Lesson
from database.models.slide import Slide
from database.schemas.slide import SlidesTableSchema

logger = logging.getLogger()


async def get_all_slides_from_lesson_by_order_fastui(lesson_id, db_session) -> list:
    slides_query = select(Slide).where(Slide.lesson_id == lesson_id)
    result = await db_session.execute(slides_query)
    slides = result.scalars().all()
    slides_dict = {slide.id: slide for slide in slides}
    ordered_slides = []
    first_slide_query = select(Lesson.first_slide_id).where(Lesson.id == lesson_id)
    result = await db_session.execute(first_slide_query)
    current_slide = result.scalar()
    index = 1
    while current_slide:
        current_slide = slides_dict.get(current_slide)
        if current_slide:
            slide_data = {
                'id': current_slide.id,
                'index': index,
                'emoji': get_slide_emoji(current_slide.slide_type),
                'text': current_slide.picture if current_slide.slide_type.value == 'image' else current_slide.text,
                'details': get_slide_details(current_slide),
                'is_exam_slide': '🎓' if current_slide.is_exam_slide else ' ',
                'edit_button': '✏️',
                'up_button': '🔼',
                'down_button': '🔽',
                'plus_button': '➕',
                'minus_button': '➖',
            }
            validated_slide = SlidesTableSchema.model_validate(slide_data)
            ordered_slides.append(validated_slide)
            current_slide = current_slide.next_slide
            index += 1
        else:
            break
    logger.info(f"Processed slides: {len(ordered_slides)}")
    return ordered_slides


async def get_all_slides_from_lesson_by_order(lesson_id, db_session):
    slides_query = select(Slide).where(Slide.lesson_id == lesson_id)
    result = await db_session.execute(slides_query)
    slides = result.scalars().all()
    slides_dict = {slide.id: slide for slide in slides}
    ordered_slides = []
    first_slide_query = select(Lesson.first_slide_id).where(Lesson.id == lesson_id)
    result = await db_session.execute(first_slide_query)
    current_slide = result.scalar()
    index = 1
    while current_slide:
        current_slide = slides_dict.get(current_slide)
        if current_slide:
            ordered_slides.append(current_slide)
            current_slide = current_slide.next_slide
            index += 1
        else:
            break
    return ordered_slides
