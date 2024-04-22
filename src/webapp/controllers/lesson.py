import logging

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.lesson import get_lesson_by_id
from database.models.lesson import Lesson
from enums import LessonStatus, PathType, SlidesMenuType
from lesson_path import LessonPath
from webapp.db import AsyncDBSession
from webapp.schemas.lesson import ActiveLessonsTableSchema, EditingLessonsTableSchema

logger = logging.getLogger()


async def get_active_lessons_fastui(db_session: AsyncDBSession):
    query = select(Lesson).group_by(Lesson.index).filter(Lesson.is_active == LessonStatus.ACTIVE)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    validated_lessons = []
    for lesson in lessons:
        lesson_data = {
            'id': lesson.id,
            'index': lesson.index,
            'title': lesson.title,
            'level': lesson.level if lesson.level else None,
            'total_slides': str(len(LessonPath(lesson.path))) if lesson.path else ' ',
            'extra_slides': str(len(LessonPath(lesson.path_extra))) if lesson.path_extra else ' ',
            'is_paid': '☑️' if lesson.is_paid else ' ',
            'errors_threshold': str(lesson.errors_threshold) + '%' if lesson.errors_threshold else ' ',
            'slides': '📖',
            'edit_button': '✏️',
            'up_button': '🔼',
            'down_button': '🔽',
            'minus_button': '➖',
        }
        validated_lesson = ActiveLessonsTableSchema.model_validate(lesson_data)
        validated_lessons.append(validated_lesson)
    logger.info(f"Processed lessons: {len(validated_lessons)}")
    return validated_lessons


async def get_editing_lessons_fastui(db_session: AsyncDBSession):
    query = select(Lesson).group_by(Lesson.created_at).filter(Lesson.is_active == LessonStatus.EDITING)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    validated_lessons = []
    for lesson in lessons:
        lesson_data = {
            'id': lesson.id,
            'title': lesson.title,
            'level': lesson.level if lesson.level else None,
            'is_paid': '☑️' if lesson.is_paid else ' ',
            'total_slides': str(len(LessonPath(lesson.path))) if lesson.path else ' ',
            'extra_slides': str(len(LessonPath(lesson.path_extra))) if lesson.path_extra else ' ',
            'errors_threshold': str(lesson.errors_threshold) + '%' if lesson.errors_threshold else ' ',
            'slides': '📖',
            'edit_button': '✏️',
            'minus_button': '➖',
            'placeholder': ' ',
        }
        validated_lesson = EditingLessonsTableSchema.model_validate(lesson_data)
        validated_lessons.append(validated_lesson)
    logger.info(f"Processed lessons: {len(validated_lessons)}")
    return validated_lessons


async def update_lesson_path(
    lesson_id: int,
    source: SlidesMenuType,
    slide_id: int,
    db_session: AsyncDBSession,
    index: int | None = None,
    mode: PathType | None = None,
) -> None:
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    match source:
        case SlidesMenuType.REGULAR:
            if index is None:
                lesson.path = str(slide_id)
            else:
                lesson.path = compose_lesson_path(index, lesson.path, mode, slide_id)
        case SlidesMenuType.EXTRA:
            if index is None:
                lesson.path_extra = str(slide_id)
            else:
                lesson.path_extra = compose_lesson_path(index, lesson.path_extra, mode, slide_id)
        case _:
            raise AssertionError(f'Unexpected source: {source}')


def compose_lesson_path(index, path, mode, slide_id) -> str:
    lesson_path = LessonPath(path)
    match mode:
        case PathType.EXISTING_PATH_NEW:
            lesson_path.add_slide(index, slide_id)
        case PathType.EXISTING_PATH_EDIT:
            lesson_path.edit_slide(index, slide_id)
    return str(lesson_path)


async def recompose_lesson_indexes(index: int, db_session: AsyncSession):
    query = (
        update(Lesson)
        .filter(
            and_(
                Lesson.is_active == LessonStatus.ACTIVE,
                Lesson.index.isnot(None),
                Lesson.index > index,
            )
        )
        .values(index=Lesson.index - 1)
    )
    await db_session.execute(query)
    await db_session.commit()
