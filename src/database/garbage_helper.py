from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from enums import LessonStatus, SessionStatus
from lesson_path import LessonPath


async def get_set_of_all_slides_in_lessons(db_session: AsyncSession) -> set[int]:
    set_of_all_slides = set()
    query = select(Lesson).filter(Lesson.is_active.in_((LessonStatus.ACTIVE, LessonStatus.EDITING)))
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    for lesson in lessons:
        add_slides_from_paths([lesson.path, lesson.path_extra], set_of_all_slides)
    return set_of_all_slides


async def get_set_of_all_slides_in_active_sessions(db_session: AsyncSession) -> set[int]:
    set_of_all_slides = set()
    query = select(Session).filter(Session.status == SessionStatus.IN_PROGRESS)
    result = await db_session.execute(query)
    sessions = result.scalars().all()
    for session in sessions:
        add_slides_from_paths([session.path, session.path_extra], set_of_all_slides)
    return set_of_all_slides


def add_slides_from_paths(paths, slide_set):
    for path in paths:
        if path:
            lesson_path = LessonPath(path).path
            slide_set.update(lesson_path)


async def delete_disabled_lessons(db_session: AsyncSession):
    query = delete(Lesson).where(Lesson.is_active == LessonStatus.DISABLED)
    await db_session.execute(query)


async def delete_unused_slides(db_session: AsyncSession):
    all_slides_in_lessons = await get_set_of_all_slides_in_lessons(db_session)
    all_slides_in_sessions = await get_set_of_all_slides_in_active_sessions(db_session)
    active_slides = all_slides_in_lessons | all_slides_in_sessions
    query = delete(Slide).where(Slide.id.notin_(active_slides))
    await db_session.execute(query)


async def collect_garbage(db_session: AsyncSession):
    await delete_disabled_lessons(db_session)
    await delete_unused_slides(db_session)
