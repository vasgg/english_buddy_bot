from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.exc import PendingRollbackError

from core.database.db import db


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
