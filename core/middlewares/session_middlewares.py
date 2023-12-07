from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.exc import PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.session_controller import get_session
from core.database.db import db


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        async with db.session_factory.begin() as db_session:
            data['db_session'] = db_session
            res = await handler(event, data)
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
