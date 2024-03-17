import logging

from sqlalchemy import select

from database.models.text import Text
from webapp.db import AsyncDBSession
from webapp.schemas.text import TextsTableSchema

logger = logging.getLogger()


async def get_text_by_id(text_id: int, session: AsyncDBSession):
    query = select(Text).where(Text.id == text_id)
    result = await session.execute(query)
    text = result.scalars().first()
    logger.info(f'processed text {text}')
    return text


async def get_texts_table_content(session: AsyncDBSession):
    query = select(Text)
    result = await session.execute(query)
    results = result.scalars().all()
    texts = []
    for text in results:
        valid_text = TextsTableSchema.model_validate(text)
        texts.append(valid_text)
    logger.info(f'processed {len(texts)} texts')
    return texts
