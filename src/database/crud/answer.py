from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.reaction import Reaction
from database.models.sticker import Sticker
from database.models.text import Text
from enums import ReactionType, StickerType

reaction_dict = {
    ReactionType.RIGHT: set(),
    ReactionType.WRONG: set(),
}


async def get_random_answer(mode: ReactionType, db_session: AsyncSession) -> str:
    if not reaction_dict[mode]:
        query = select(Reaction.text).filter(Reaction.type == mode)
        result = await db_session.execute(query)
        reaction_dict[mode].update(result.scalars().all())
    return reaction_dict[mode].pop()


async def get_random_sticker_id(mode: StickerType, db_session: AsyncSession) -> str:
    query = select(Sticker.sticker_id).filter(Sticker.sticker_type == mode).order_by(func.random()).limit(1)
    result = await db_session.execute(query)
    return result.scalar()


async def get_text_by_prompt(prompt: str, db_session: AsyncSession) -> str:
    query = select(Text.text).filter(Text.prompt == prompt)
    result = await db_session.execute(query)
    check = result.scalar_one_or_none()
    if not check:
        return f'Данные по запросу "{prompt}" отсутствуют в базе.'
    return check
