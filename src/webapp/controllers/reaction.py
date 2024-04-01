import logging

from database.models.reaction import Reaction
from enums import ReactionType
from sqlalchemy import select
from webapp.db import AsyncDBSession
from webapp.schemas.reaction import ReactionsTableSchema

logger = logging.getLogger()


async def get_reactions_table_content(reaction_type: ReactionType, session: AsyncDBSession):
    query = select(Reaction).filter(Reaction.type == reaction_type)
    result = await session.execute(query)
    results = result.scalars().all()
    reactions = []
    for reaction in results:
        valid_reaction = ReactionsTableSchema.model_validate(reaction)
        reactions.append(valid_reaction)
    logger.info(f'processed {len(reactions)} {reaction_type.value} reactions')
    return reactions


async def delete_reaction_by_id(reaction_id: int, db_session: AsyncDBSession) -> None:
    query = select(Reaction).filter(Reaction.id == reaction_id)
    result = await db_session.execute(query)
    await db_session.delete(result.scalar())


async def get_reaction_by_id(reaction_id: int, db_session: AsyncDBSession) -> Reaction:
    query = select(Reaction).filter(Reaction.id == reaction_id)
    result = await db_session.execute(query)
    return result.scalar()
