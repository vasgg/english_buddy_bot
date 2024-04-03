import contextlib
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from database.crud.session import get_session
from database.database_connector import DatabaseConnector
from sqlalchemy.exc import PendingRollbackError

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from sqlalchemy.ext.asyncio import AsyncSession


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
            with contextlib.suppress(PendingRollbackError):
                await db_session.commit()

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
        # TODO: calculate from db in case of missing
        db_session: AsyncSession = data['db_session']
        user_session = await get_session(session_id, db_session)
        data['session'] = user_session
        res = await handler(event, data)
        return res
