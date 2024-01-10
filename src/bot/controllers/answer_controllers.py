from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.answer import Answer
from bot.database.models.sticker import Sticker
from bot.database.models.text import Text
from bot.resources.enums import AnswerType, StickerType


async def get_random_answer(mode: AnswerType, db_session: AsyncSession) -> str:
    query = select(Answer.text).filter(Answer.answer_type == mode).order_by(func.random()).limit(1)
    result = await db_session.execute(query)
    return result.scalar()


async def get_random_sticker_id(mode: StickerType, db_session: AsyncSession) -> str:
    query = select(Sticker.sticker_id).filter(Sticker.sticker_type == mode).order_by(func.random()).limit(1)
    result = await db_session.execute(query)
    return result.scalar()


async def get_text_by_prompt(prompt: str, db_session: AsyncSession) -> str:
    query = select(Text.text).filter(Text.prompt == prompt)
    result = await db_session.execute(query)
    return result.scalar()
