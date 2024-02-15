from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.database_connector import DatabaseConnector

# todo: move from global scope
# could open connection from init, which is bad
db = DatabaseConnector(url=settings.aiosqlite_db_url, echo=settings.db_echo)


async def get_db_session() -> AsyncSession:
    async with db.session_factory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


AsyncDBSession = Annotated[AsyncSession, Depends(get_db_session)]
