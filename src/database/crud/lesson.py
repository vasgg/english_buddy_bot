from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from enums import SessionStatus, SlideType
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_lesson_by_id(lesson_id: int, db_session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.id == lesson_id)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_lesson_by_index(lesson_index: int, db_session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.index == lesson_index)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_lessons(db_session: AsyncSession) -> list[Lesson]:
    query = select(Lesson).filter(Lesson.is_active).group_by(Lesson.index)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    return list(lessons)


async def get_lessons_with_greater_index(index: int, db_session: AsyncSession) -> list[Lesson]:
    query = select(Lesson).filter(Lesson.is_active, Lesson.index > index).group_by(Lesson.index)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    return list(lessons)


async def get_completed_lessons_from_sessions(user_id: int, db_session: AsyncSession) -> set[int]:
    query = select(Session.lesson_id).filter(Session.status == SessionStatus.COMPLETED, Session.user_id == user_id)
    result = await db_session.execute(query)
    return set(result.scalars().all())


async def get_all_exam_slides_id_in_slides(lesson_id: int, db_session: AsyncSession) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.lesson_id == lesson_id,
        Slide.is_exam_slide,
        Slide.slide_type.in_(all_questions_slide_types),
    )
    result = await db_session.execute(query)
    return set(result.scalars().all()) if result else {}
