from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from database.crud.user import add_user_to_db, get_user_from_db


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        session = data['db_session']
        user = await get_user_from_db(event, session)
        data['is_new_user'] = False
        if not user:
            user = await add_user_to_db(event.from_user, session)
            data['is_new_user'] = True
        data['user'] = user
        return await handler(event, data)
