from database.models.quiz_answer_log import QuizAnswerLog
from enums import SlideType
from sqlalchemy.ext.asyncio import AsyncSession


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
