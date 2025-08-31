from sqlalchemy import Result, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from enums import LessonStatus, SessionStatus, SlideType


async def get_lesson_by_id(lesson_id: int, db_session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.id == lesson_id)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_lesson_by_index(lesson_index: int, db_session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.index == lesson_index)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_active_lessons(db_session: AsyncSession) -> list[Lesson]:
    query = select(Lesson).filter(Lesson.is_active == LessonStatus.ACTIVE).group_by(Lesson.index)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    return list(lessons)


async def get_active_and_editing_lessons(db_session: AsyncSession) -> list[Lesson]:
    query = select(Lesson).filter(Lesson.is_active.in_((LessonStatus.ACTIVE, LessonStatus.EDITING)))
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    active_lessons = [lesson for lesson in lessons if lesson.is_active == LessonStatus.ACTIVE]
    editing_lessons = [lesson for lesson in lessons if lesson.is_active == LessonStatus.EDITING]
    sorted_active = sorted(active_lessons, key=lambda x: (x.index is None, x.index))
    sorted_editing = sorted(editing_lessons, key=lambda x: x.created_at)
    sorted_lessons = sorted_active + sorted_editing
    return sorted_lessons


async def update_lesson_status(lesson_id: int, mode: LessonStatus, db_session: AsyncSession):
    query = update(Lesson).filter(Lesson.id == lesson_id).values(is_active=mode, index=None)
    await db_session.execute(query)
    await db_session.commit()


async def get_completed_lessons_from_sessions(user_id: int, db_session: AsyncSession) -> set[int]:
    query = select(Session.lesson_id).filter(Session.status == SessionStatus.COMPLETED, Session.user_id == user_id)
    result = await db_session.execute(query)
    return set(result.scalars().all())


async def get_completed_lessons_recent_first(user_id: int, db_session: AsyncSession) -> list[tuple[int, "datetime"]]:
    subq = (
        select(
            Session.lesson_id.label('lesson_id'),
            func.max(Session.created_at).label('last_completed_at'),
        )
        .filter(Session.status == SessionStatus.COMPLETED, Session.user_id == user_id)
        .group_by(Session.lesson_id)
        .subquery()
    )
    query = select(subq.c.lesson_id, subq.c.last_completed_at).order_by(subq.c.last_completed_at.desc())
    result = await db_session.execute(query)
    return list(result.all())


async def get_all_exam_slides_id_in_slides(lesson_id: int, db_session: AsyncSession) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.lesson_id == lesson_id,
        Slide.is_exam_slide,
        Slide.slide_type.in_(all_questions_slide_types),
    )
    result = await db_session.execute(query)
    return set(result.scalars().all()) if result else {}
