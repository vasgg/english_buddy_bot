import logging

from sqlalchemy import select

from database.db import AsyncDBSession
from database.models.lesson import Lesson
from database.schemas.lesson import LessonsTableSchema

logger = logging.getLogger()


async def get_lessons_fastui(db_session: AsyncDBSession):
    query = select(Lesson).group_by(Lesson.index).filter(Lesson.is_active)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    validated_lessons = []
    for index, lesson in enumerate(lessons, start=1):
        lesson_data = {
            'id': lesson.id,
            'index': index,
            'title': lesson.title,
            'level': lesson.level if lesson.level else None,
            'is_paid': '☑️' if lesson.path.split('.')[0] == '1' else ' ',
            'exam_slide_id': lesson.exam_slide_id if lesson.exam_slide_id else None,
            'total_slides': str(len(lesson.path.split('.')) - 1) if lesson.path else ' ',
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
