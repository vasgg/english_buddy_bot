import logging

from sqlalchemy import select

from database.db import AsyncDBSession
from database.models.text import Text
from database.schemas.text import TextsTableSchema

logger = logging.getLogger()


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
