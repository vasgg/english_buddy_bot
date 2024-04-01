from typing import Annotated

from database.database_connector import DatabaseConnector
from database.tables_helper import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
