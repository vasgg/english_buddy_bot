from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models.session import Session
from core.database.models.session_log import SessionLog
from core.resources.enums import CountQuizSlidesMode, SessionStatus, SlideType


async def get_lesson_progress(
    user_id: int, lesson_id: int, db_session: AsyncSession
) -> int:
    query = select(Session.current_slide_id).filter(
        Session.user_id == user_id,
        Session.lesson_id == lesson_id,
        Session.status == SessionStatus.IN_PROGRESS,
    )
    result: Result = await db_session.execute(query)
    user_progress = result.scalar_one_or_none()
    return user_progress


async def get_current_session(
    user_id: int, lesson_id: int, db_session: AsyncSession
) -> Session | None:
    query = select(Session).filter(
        Session.user_id == user_id,
        Session.lesson_id == lesson_id,
        Session.status == SessionStatus.IN_PROGRESS,
    )
    result: Result = await db_session.execute(query)
    return result.scalar_one_or_none()


async def get_session(session_id: int, db_session: AsyncSession) -> Session | None:
    session = await db_session.get(Session, session_id)
    return session


async def update_session_status(
    session_id: int, new_status: SessionStatus, db_session: AsyncSession
) -> None:
    query = update(Session).filter(Session.id == session_id).values(status=new_status)
    await db_session.execute(query)


async def count_distinct_slides_by_type(
    session_id: int,
    mode: CountQuizSlidesMode,
    db_session: AsyncSession,
    slide_type: SlideType = None,
) -> int:
    match mode:
        case CountQuizSlidesMode.WITH_TYPE:
            if not slide_type:
                raise ValueError("in WITH_TYPE mode you must provide Slide type")
            query = select(func.count(SessionLog.slide_id.distinct())).filter(
                SessionLog.session_id == session_id, SessionLog.slide_type == slide_type
            )
        case CountQuizSlidesMode.WITHOUT_TYPE:
            if slide_type:
                query = select(func.count(SessionLog.slide_id.distinct())).filter(
                    SessionLog.session_id == session_id,
                    SessionLog.slide_type != slide_type,
                )
            else:
                query = select(func.count(SessionLog.slide_id.distinct())).filter(
                    SessionLog.session_id == session_id
                )
        case _:
            assert False, f"Unknown mode: {mode}"

    result = await db_session.execute(query)
    return result.scalar()


async def count_errors_in_slides_by_type(
    session_id: int,
    mode: CountQuizSlidesMode,
    db_session: AsyncSession,
    slide_type: SlideType = None,
) -> int:
    subquery = (
        select(
            SessionLog.slide_type,
            SessionLog.slide_id,
            (func.count(SessionLog.slide_id) - 1).label("errors"),
        )
        .where(SessionLog.session_id == session_id)
        .group_by(SessionLog.slide_type, SessionLog.slide_id)
        .having(func.count(SessionLog.slide_id) > 1)
        .subquery()
    )
    match mode:
        case CountQuizSlidesMode.WITH_TYPE:
            if not slide_type:
                raise ValueError("in WITH_TYPE mode you must provide Slide type")
            query = select(func.sum(subquery.c.errors)).where(
                subquery.c.slide_type == slide_type
            )
        case CountQuizSlidesMode.WITHOUT_TYPE:
            if slide_type:
                query = select(func.sum(subquery.c.errors)).where(
                    subquery.c.slide_type != slide_type
                )
            else:
                query = select(func.sum(subquery.c.errors))
        case _:
            assert False, f"Unknown mode: {mode}"
    result = await db_session.execute(query)
    errors = result.scalar_one_or_none()
    return errors if errors is not None else 0
