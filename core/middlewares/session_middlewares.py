from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.exc import PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.session_controller import get_current_session
from core.database.db import db
from core.database.models import Session, User


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
        # db_session: AsyncSession = data['db_session']
        # user: User = data['user']

        # TODO: read user sessison by user.current_session_id
        data['session'] = session
        res = await handler(event, data)
        return res
