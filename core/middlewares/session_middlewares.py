from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.exc import PendingRollbackError

from core.controllers.session_controller import get_current_session
from core.database.db import db
from core.database.models import User


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        async with db.session_factory.begin() as session:
            data['session'] = session
            res = await handler(event, data)
            try:
                await session.commit()
            except PendingRollbackError:
                ...
            return res


class UserSessionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
            session = data['session']
            user: User = data['user']
            # TODO: read user sessison by user.current_session_id
            data['user_session'] = user_session
            return await handler(event, data)
