from sqlalchemy import Float, cast, func, select
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


async def get_top_error_slides(session: AsyncSession):
    query = (
        select(
            QuizAnswerLog.slide_id.label("slide_id"),
            func.count().filter(QuizAnswerLog.is_correct).label("correct"),
            func.count().filter(~QuizAnswerLog.is_correct).label("wrong"),
            (func.count().filter(QuizAnswerLog.is_correct) / cast(func.count(), Float)).label("correctness_rate"),
        )
        .group_by(QuizAnswerLog.slide_id)
        .order_by((func.count().filter(QuizAnswerLog.is_correct) / cast(func.count(), Float)))
    )
    result = await session.execute(query)
    slides_with_errors = result.fetchall()
    return slides_with_errors
