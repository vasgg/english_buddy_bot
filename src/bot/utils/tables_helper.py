import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine

from database.models.base import Base

# noinspection PyUnresolvedReferences
import database.models.complete_lesson

# noinspection PyUnresolvedReferences
import database.models.lesson

# noinspection PyUnresolvedReferences
import database.models.reaction

# noinspection PyUnresolvedReferences
import database.models.session

# noinspection PyUnresolvedReferences
import database.models.session_log

# noinspection PyUnresolvedReferences
import database.models.slide

# noinspection PyUnresolvedReferences
import database.models.sticker

# noinspection PyUnresolvedReferences
import database.models.text

# noinspection PyUnresolvedReferences
import database.models.user


async def create_or_drop_db(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        # await conn.run_sync(Base.metadata.drop_all)


if __name__ == '__main__':
    from bot.database.db import db

    asyncio.run(create_or_drop_db(db.engine))
