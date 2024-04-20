from database.crud.lesson import get_lesson_by_id
from database.crud.quiz_answer import get_top_error_slides
from database.crud.slide import get_slide_by_id
from enums import SlidesMenuType
from lesson_path import LessonPath
from webapp.controllers.misc import get_slide_emoji
from webapp.db import AsyncDBSession
from webapp.schemas.statistics import SlidesStatisticsTableSchema


async def get_errors_stats_table_content(limit: int, db_session: AsyncDBSession) -> list:
    slides_by_errors = await get_top_error_slides(db_session)
    stats = []
    for i in slides_by_errors:
        slide = await get_slide_by_id(i.slide_id, db_session)
        lesson = await get_lesson_by_id(slide.lesson_id, db_session)
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
        link = f'/slides/edit/{source}/{index + 1}/{slide.id}/'
        slide_data = {
            'slide_type': get_slide_emoji(slide.slide_type),
            'is_exam_slide': '🎓' if slide.is_exam_slide else ' ',
            'slide_id': slide.id,
            'lesson_title': lesson.title,
            'count_correct': str(i.correct),
            'count_wrong': str(i.wrong),
            'icon': '✏️',
            'link': link,
            'correctness_rate': f'{i.correctness_rate * 100:.0f}%',
        }
        validated_slide = SlidesStatisticsTableSchema.model_validate(slide_data)
        stats.append(validated_slide)
        if len(stats) == limit:
            break
    return stats
