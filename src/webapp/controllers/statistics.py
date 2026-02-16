from database.crud.lesson import get_lesson_by_id
from database.crud.quiz_answer import get_top_error_slides
from database.crud.session import get_sessions_statistics
from database.crud.slide import get_slide_by_id
from enums import SessionStatus, SlidesMenuType
from lesson_path import LessonPath
from webapp.controllers.misc import get_slide_emoji
from webapp.db import AsyncDBSession
from webapp.schemas.statistics import SessionStatistics, SessionsStatisticsTableSchema, SlidesStatisticsTableSchema


async def get_errors_stats_table_content(limit: int, db_session: AsyncDBSession) -> list:
    slides_by_errors = await get_top_error_slides(db_session)
    stats = []
    for i in slides_by_errors:
        slide = await get_slide_by_id(i.slide_id, db_session)
        if slide is None:
            continue
        lesson = await get_lesson_by_id(slide.lesson_id, db_session)
        if lesson is None:
            continue
        lesson_path = LessonPath(lesson.path).path
        lesson_path_extra = LessonPath(lesson.path_extra).path
        try:
            index = lesson_path.index(i.slide_id)
            source = SlidesMenuType.REGULAR
        except ValueError:
            try:
                index = lesson_path_extra.index(i.slide_id)
                source = SlidesMenuType.EXTRA
            except ValueError:
                continue
        link = f"/slides/edit/{source}/{slide.slide_type}/{slide.id}/{index + 1}/"
        slide_data = {
            "slide_type": get_slide_emoji(slide.slide_type),
            "is_exam_slide": "🎓" if slide.is_exam_slide else " ",
            "slide_id": str(slide.id),
            "lesson_title": lesson.title,
            "count_correct": str(i.correct),
            "count_wrong": str(i.wrong),
            "icon": "✏️",
            "link": link,
            "correctness_rate": f"{i.correctness_rate * 100:.0f}%",
        }
        validated_slide = SlidesStatisticsTableSchema.model_validate(slide_data)
        stats.append(validated_slide)
        if len(stats) == limit:
            break
    return stats


async def get_session_stats(db_session):
    session_stats = SessionStatistics(
        all_sessions={"description": "Всего сессий", "value": await get_sessions_statistics(db_session)},
        completed={
            "description": "Завершено сессий",
            "value": await get_sessions_statistics(db_session, status=SessionStatus.COMPLETED),
        },
        in_progress={
            "description": "Сессий в процессе",
            "value": await get_sessions_statistics(db_session, status=SessionStatus.IN_PROGRESS),
        },
        aborted={
            "description": "Отменено сессий",
            "value": await get_sessions_statistics(db_session, status=SessionStatus.ABORTED),
        },
    )
    rows = []
    all_sessions_schema = SessionsStatisticsTableSchema.model_validate(session_stats.all_sessions)
    completed_schema = SessionsStatisticsTableSchema.model_validate(session_stats.completed)
    in_progress_schema = SessionsStatisticsTableSchema.model_validate(session_stats.in_progress)
    aborted_schema = SessionsStatisticsTableSchema.model_validate(session_stats.aborted)
    rows.extend([all_sessions_schema, completed_schema, in_progress_schema, aborted_schema])
    return rows
