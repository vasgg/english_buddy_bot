import logging

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from database.crud.quiz_answer import get_errors_count
from database.crud.session import get_sessions_statistics
from database.crud.user import get_users_count
from enums import SessionStatus
from webapp.controllers.statistics import get_errors_stats_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.main_component import get_common_content
from webapp.schemas.statistics import SessionStatistics, SessionsStatisticsTableSchema

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def statistics_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    users_count = await get_users_count(db_session)
    errors_count = await get_errors_count(db_session)

    session_stats = SessionStatistics(
        all_sessions={'description': 'Всего сессий', 'value': await get_sessions_statistics(db_session)},
        completed={'description': 'Завершено сессий', 'value': await get_sessions_statistics(db_session, status=SessionStatus.COMPLETED)},
        in_progress={'description': 'Сессий в процессе', 'value': await get_sessions_statistics(db_session, status=SessionStatus.IN_PROGRESS)},
        aborted={'description': 'Отменено сессий', 'value': await get_sessions_statistics(db_session, status=SessionStatus.ABORTED)},
    )
    errors_stats = await get_errors_stats_table_content(db_session)
    rows = []
    all_sessions_schema = SessionsStatisticsTableSchema.model_validate(session_stats.all_sessions)
    completed_schema = SessionsStatisticsTableSchema.model_validate(session_stats.completed)
    in_progress_schema = SessionsStatisticsTableSchema.model_validate(session_stats.in_progress)
    aborted_schema = SessionsStatisticsTableSchema.model_validate(session_stats.aborted)
    rows.extend([all_sessions_schema, completed_schema, in_progress_schema, aborted_schema])

    logger.info('statistics router called')
    return get_common_content(
        c.Heading(text='Пользователи', level=4),
        c.Paragraph(text=f'Всего пользователей: {users_count}'),
        c.Heading(text='Сессии', level=4),
        c.Table(data=rows,
                columns=[
                    DisplayLookup(field='description', title='описание'),
                    DisplayLookup(field='value', title='значение'),
                ],
                ),
        c.Heading(text='Ошибки', level=4),
        c.Paragraph(text=f'Всего ошибок в слайдах: {errors_count}'),
        c.Heading(text='Топ слайдов по количеству ошибок: ', level=4),
        c.Paragraph(text=' '),
        c.Table(data=errors_stats,
                columns=[
                    DisplayLookup(field='slide_type', table_width_percent=3, title=' '),
                    DisplayLookup(field='is_exam_slide', table_width_percent=3, title=' '),
                    DisplayLookup(field='slide_id', title='номер слайда', table_width_percent=30),
                    DisplayLookup(field='lesson_title', title='название урока', table_width_percent=30),
                    DisplayLookup(field='value', title='количество ошибок'),
                    DisplayLookup(field='icon', table_width_percent=3, title=' ',
                                  on_click=GoToEvent(url='{link}'),
                                  ),
                ],
                ),

        title='Статистика',
    )
