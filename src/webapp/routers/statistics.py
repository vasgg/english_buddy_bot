import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastui import AnyComponent, FastUI

from config import Settings, get_settings
from database.crud.user import get_users_count
from webapp.controllers.statistics import get_errors_stats_table_content, get_session_stats
from webapp.db import AsyncDBSession
from webapp.routers.components.components import get_statistics_page

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def statistics_page(
    settings: Annotated[Settings, Depends(get_settings)], db_session: AsyncDBSession
) -> list[AnyComponent]:
    users_count = await get_users_count(db_session)
    session_stats = await get_session_stats(db_session)
    errors_stats = await get_errors_stats_table_content(limit=settings.TOP_BAD_SLIDES_COUNT, db_session=db_session)
    logger.info('statistics router called')
    return get_statistics_page(users_count, session_stats, errors_stats)
