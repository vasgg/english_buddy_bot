from database.models.complete_lesson import CompleteLesson
from database.models.lesson import Lesson
from database.models.slide import Slide
from enums import SlideType
from sqlalchemy import Result, select, update
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


async def add_completed_lesson_to_db(user_id: int, lesson_id: int, session_id: int, db_session: AsyncSession) -> None:
    completed_lesson = CompleteLesson(
        user_id=user_id,
        lesson_id=lesson_id,
        session_id=session_id,
    )
    db_session.add(completed_lesson)
    await db_session.flush()


async def get_completed_lessons(user_id: int, db_session: AsyncSession) -> set[int]:
    query = select(CompleteLesson.lesson_id).filter(CompleteLesson.user_id == user_id)
    result = await db_session.execute(query)
    return set(result.scalars().all())


async def get_all_exam_slides_id_in_lesson(lesson_id: int, db_session: AsyncSession) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.lesson_id == lesson_id, Slide.is_exam_slide, Slide.slide_type.in_(all_questions_slide_types),
    )
    result = await db_session.execute(query)
    return set(result.scalars().all()) if result else {}


async def update_lesson_first_slide(lesson_id: int, first_slide_id: int, db_session):
    await db_session.execute(update(Lesson).where(Lesson.id == lesson_id).values(first_slide_id=first_slide_id))


async def update_lesson_exam_slide(lesson_id: int, exam_slide_id: int, db_session):
    await db_session.execute(update(Lesson).where(Lesson.id == lesson_id).values(exam_slide_id=exam_slide_id))


async def reset_index_for_all_lessons(db_session):
    await db_session.execute(update(Lesson).values(index=None))


async def update_lesson_index(lesson_id: int, index: int | None, db_session: AsyncSession):
    await db_session.execute(update(Lesson).where(Lesson.id == lesson_id).values(index=index))


async def update_lesson_parameter(lesson_id: int, parameter_name: str, parameter_value: str, db_session: AsyncSession):
    query = update(Lesson).filter(Lesson.id == lesson_id).values(**{parameter_name: parameter_value})
    await db_session.execute(query)
