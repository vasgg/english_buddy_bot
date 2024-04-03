from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.internal.blink1 import blink1_green
from bot.internal.google_sheet import sheet_update
from config import get_settings
from database.crud.user import add_user_to_db, get_user_from_db
from enums import Stage


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        session = data['db_session']
        user = await get_user_from_db(event.from_user.id, session)
        data['is_new_user'] = False
        if not user:
            user = await add_user_to_db(event.from_user, session)
            data['is_new_user'] = True
            if get_settings().STAGE == Stage.PROD:
                await blink1_green()
                await sheet_update('C3', user.id)
        data['user'] = user
        return await handler(event, data)
