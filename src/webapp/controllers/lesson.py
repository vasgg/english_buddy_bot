import logging

from sqlalchemy import select

from database.models.lesson import Lesson
from webapp.db import AsyncDBSession
from webapp.schemas.lesson import LessonsTableSchema

logger = logging.getLogger()


async def get_lessons_fastui(db_session: AsyncDBSession):
    query = select(Lesson).group_by(Lesson.index).filter(Lesson.is_active)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    validated_lessons = []
    for lesson in lessons:
        lesson_data = {
            'id': lesson.id,
            'index': lesson.index,
            'title': lesson.title,
            'level': lesson.level if lesson.level else None,
            'is_paid': '☑️' if lesson.is_paid else ' ',
            'total_slides': str(len(lesson.path.split('.'))) if lesson.path else ' ',
            'extra_slides': str(len(lesson.path_extra.split('.'))) if lesson.path_extra else ' ',
            'errors_threshold': str(lesson.errors_threshold) + '%' if lesson.errors_threshold else ' ',
            'slides': '📖',
            'edit_button': '✏️',
            'up_button': '🔼',
            'down_button': '🔽',
            'plus_button': '➕',
            'minus_button': '➖',
        }
        validated_lesson = LessonsTableSchema.model_validate(lesson_data)
        validated_lessons.append(validated_lesson)
    logger.info(f"Processed lessons: {len(validated_lessons)}")
    return validated_lessons
