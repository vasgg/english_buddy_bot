import logging

from sqlalchemy import select

from database.db import AsyncDBSession
from database.models.lesson import Lesson
from database.schemas.lesson import LessonsTableSchema

logger = logging.getLogger()


async def get_lessons_fastui(db_session: AsyncDBSession):
    query = select(Lesson).group_by(Lesson.index)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    validated_lessons = []
    for lesson in lessons:
        validated_lesson = LessonsTableSchema.model_validate(lesson)
        validated_lessons.append(validated_lesson)
    return validated_lessons
