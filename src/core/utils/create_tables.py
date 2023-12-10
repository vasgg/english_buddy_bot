import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine

# noinspection PyUnresolvedReferences
import core.database.models.answer
# noinspection PyUnresolvedReferences
import core.database.models.lesson
# noinspection PyUnresolvedReferences
import core.database.models.session
# noinspection PyUnresolvedReferences
import core.database.models.session_log
# noinspection PyUnresolvedReferences
import core.database.models.slide
# noinspection PyUnresolvedReferences
import core.database.models.user
# noinspection PyUnresolvedReferences
import core.database.models.user_complete_lesson
from core.database.models.base import Base


async def create_or_drop_db(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        # await conn.run_sync(Base.metadata.drop_all)


if __name__ == "__main__":
    from core.database.db import db

    asyncio.run(create_or_drop_db(db.engine))
