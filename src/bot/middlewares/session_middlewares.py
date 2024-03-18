from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.exc import PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.session import get_session
from database.database_connector import DatabaseConnector


class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, db: DatabaseConnector):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with self.db.session_factory() as db_session:
            # TODO: mb change to db_session factory
            data['db_session'] = db_session
            res = await handler(event, data)
            # TODO: probably,check how session handles it
            # check how commit behaves
            try:
                await db_session.commit()
            except PendingRollbackError:
                ...
            return res


class SessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        state: FSMContext = data['state']
        state_data = await state.get_data()
        session_id = state_data['session_id']
        db_session: AsyncSession = data['db_session']
        user_session = await get_session(session_id, db_session)
        data['session'] = user_session
        res = await handler(event, data)
        return res
