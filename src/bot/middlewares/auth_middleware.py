from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from config import get_settings
from database.crud.user import add_user_to_db, get_user_from_db_by_tg_id, touch_user_activity

settings = get_settings()


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        from_user = event.from_user
        if from_user is None:
            return await handler(event, data)
        session = data["db_session"]
        user = await get_user_from_db_by_tg_id(from_user.id, session)
        data["is_new_user"] = False
        if not user:
            user = await add_user_to_db(from_user, session)
            await session.commit()
            data["is_new_user"] = True
            # if settings.STAGE == Stage.PROD:
            #     await blink1_green()
            #     await sheet_update('C3', user.id)
        else:
            user.fullname = from_user.full_name
            user.username = from_user.username
            await touch_user_activity(user.id, datetime.now(timezone.utc), session)
        data["user"] = user
        return await handler(event, data)
