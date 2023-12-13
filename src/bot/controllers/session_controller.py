from sqlalchemy import Result, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.session import Session
from bot.database.models.session_log import SessionLog
from bot.resources.enums import EventType, SessionStatus, SlideType


async def get_lesson_progress(user_id: int, lesson_id: int, db_session: AsyncSession) -> int:
    query = select(Session.current_slide_id).filter(
        Session.user_id == user_id,
        Session.lesson_id == lesson_id,
        Session.status == SessionStatus.IN_PROGRESS,
    )
    result: Result = await db_session.execute(query)
    user_progress = result.scalar_one_or_none()
    return user_progress


async def get_current_session(user_id: int, lesson_id: int, db_session: AsyncSession) -> Session | None:
    query = select(Session).filter(
        Session.user_id == user_id,
        Session.lesson_id == lesson_id,
        Session.status == SessionStatus.IN_PROGRESS,
    )
    result: Result = await db_session.execute(query)
    return result.scalar_one_or_none()


async def get_last_session_with_progress(user_id: int, db_session: AsyncSession) -> Session | None:
    query = (
        select(Session)
        .filter(
            Session.user_id == user_id,
            Session.status == SessionStatus.IN_PROGRESS,
        )
        .order_by(Session.created_at.desc())
        .limit(1)
    )
    result = await db_session.execute(query)
    last_session = result.scalars().first()
    return last_session


async def get_session(session_id: int, db_session: AsyncSession) -> Session | None:
    session = await db_session.get(Session, session_id)
    return session


async def update_session_status(session_id: int, new_status: SessionStatus, db_session: AsyncSession) -> None:
    query = update(Session).filter(Session.id == session_id).values(status=new_status)
    await db_session.execute(query)


async def get_wrong_answers_counter(session_id: int, slide_id: int, db_session: AsyncSession) -> int:
    query = select(func.count(SessionLog.id)).filter(
        SessionLog.session_id == session_id,
        SessionLog.slide_id == slide_id,
        ~SessionLog.is_correct,
    )
    result = await db_session.execute(query)
    return result.scalar()


async def log_quiz_answer(
    session: Session, is_correct: bool | None, mode: EventType, event, slide, db_session: AsyncSession
):
    match mode:
        case EventType.MESSAGE:
            data = event.text
        case EventType.CALLBACK_QUERY:
            if ":" in event.data:
                data = event.data.split(":")[-1]
            else:
                data = event.data
        case EventType.HINT:
            data = "show_hint"
        case EventType.CONTINUE:
            data = "continue"
        case _:
            assert False, f"Unknown event type: {mode}"
    json_event = event.model_dump_json(exclude_unset=True)
    session_log = SessionLog(
        session_id=session.id,
        slide_id=session.current_slide_id,
        slide_type=slide.slide_type,
        data=data,
        is_correct=is_correct,
        update=json_event,
    )
    db_session.add(session_log)


async def get_all_questions_in_session(session_id: int, db_session: AsyncSession) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(SessionLog.slide_id).filter(
        SessionLog.session_id == session_id, SessionLog.slide_type.in_(all_questions_slide_types)
    )
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()} if result else {}


async def get_hints_shown_counter_in_session(session_id: int, db_session: AsyncSession) -> int:
    query = select(func.count(SessionLog.id)).filter(
        SessionLog.session_id == session_id, SessionLog.data == "show_hint"
    )
    result = await db_session.execute(query)
    return result.scalar()


async def count_errors_in_session(session_id, slides_set: set[int], db_session: AsyncSession) -> int:
    subquery = (
        select(SessionLog.slide_id)
        .filter(SessionLog.session_id == session_id, SessionLog.slide_id.in_(slides_set), ~SessionLog.is_correct)
        .distinct()
        .subquery()
    )
    query = select(func.count()).select_from(subquery)
    result = await db_session.execute(query)
    return result.scalar()
