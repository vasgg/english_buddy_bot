from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.quiz_answer_log import QuizAnswerLog
from enums import SlideType


async def log_quiz_answer(
        session_id: int,
        slide_id: int,
        slide_type: SlideType,
        is_correct: bool,
        db_session: AsyncSession,
):
    session_log = QuizAnswerLog(
        session_id=session_id,
        slide_id=slide_id,
        slide_type=slide_type,
        is_correct=is_correct,
    )
    db_session.add(session_log)
    await db_session.flush()


async def get_errors_count(db_session: AsyncSession) -> int:
    query = select(func.count()).select_from(QuizAnswerLog).filter(~QuizAnswerLog.is_correct)
    result = await db_session.execute(query)
    return result.scalar()


async def get_top_error_slides(session: AsyncSession, limit: int = 1000):
    query = (
        select(
            QuizAnswerLog.slide_id,
            func.count(QuizAnswerLog.slide_id).label('error_count'),
        )
        .where(~QuizAnswerLog.is_correct)
        .group_by(QuizAnswerLog.slide_id)
        .order_by(func.count(QuizAnswerLog.slide_id).desc())
        .limit(limit)
    )

    result = await session.execute(query)
    slides_with_errors = result.fetchall()
    return slides_with_errors
