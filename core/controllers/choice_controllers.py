from random import choice

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Answer
from core.resources.enums import AnswerType


def get_random_sticker_id(collection: tuple[str]) -> str:
    random_sticker_id = choice(collection)
    return random_sticker_id


async def get_random_answer(mode: AnswerType, db_session: AsyncSession) -> str:
    query = select(Answer.text).filter(Answer.answer_type == mode).order_by(func.random()).limit(1)
    result = await db_session.execute(query)
    answer = result.scalar()
    return answer

