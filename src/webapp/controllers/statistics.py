from database.crud.lesson import get_lesson_by_id
from database.crud.quiz_answer import get_top_error_slides
from database.crud.slide import get_slide_by_id
from enums import SlidesMenuType
from webapp.controllers.misc import get_slide_emoji
from webapp.db import AsyncDBSession
from webapp.schemas.statistics import SlidesStatisticsTableSchema


async def get_errors_stats_table_content(db_session: AsyncDBSession) -> list:
    slides_by_errors = await get_top_error_slides(db_session)
    print(slides_by_errors)
    stats = []
    for i in slides_by_errors:
        slide = await get_slide_by_id(i[0], db_session)
        lesson = await get_lesson_by_id(slide.lesson_id, db_session)
        lesson_path = [int(slide_id) for slide_id in lesson.path.split('.')]
        lesson_path_extra = [int(slide_id) for slide_id in lesson.path_extra.split('.')] if lesson.path_extra else []
        source = SlidesMenuType.REGULAR if i[0] in lesson_path else SlidesMenuType.EXTRA
        try:
            index = lesson_path.index(i[0]) if i[0] in lesson_path else lesson_path_extra.index(i[0])
        except ValueError:
            continue
        link = f'/slides/edit/{source}/{index + 1}/{slide.id}/'
        slide_data = {
            'slide_type': get_slide_emoji(slide.slide_type),
            'is_exam_slide': '🎓' if slide.is_exam_slide else ' ',
            'slide_id': slide.id,
            'lesson_index': lesson.index,
            'value': i[1],
            'icon': '✏️',
            'link': link,
        }
        validated_slide = SlidesStatisticsTableSchema.model_validate(slide_data)
        stats.append(validated_slide)
        limit = 10
        if len(stats) == limit:
            break
    return stats
