from sqlalchemy.ext.asyncio import AsyncEngine

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
from config import get_settings
from database.database_connector import DatabaseConnector
from database.models.base import Base


async def create_or_drop_db(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        # await conn.run_sync(Base.metadata.drop_all)


def get_db() -> DatabaseConnector:
    settings = get_settings()
    return DatabaseConnector(url=settings.aiosqlite_db_url, echo=settings.db_echo)


if __name__ == '__main__':
    import asyncio

    db = get_db()
    asyncio.run(create_or_drop_db(db.engine))
