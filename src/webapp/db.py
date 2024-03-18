from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database.database_connector import DatabaseConnector


# todo: move from global scope
# could open connection from init, which is bad
def get_db():
    return DatabaseConnector(url=get_settings().aiosqlite_db_url, echo=get_settings().db_echo)


AsyncDB = Annotated[DatabaseConnector, Depends(get_db)]


async def get_db_session(connector: AsyncDB) -> AsyncSession:
    async with connector.session_factory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


AsyncDBSession = Annotated[AsyncSession, Depends(get_db_session)]
