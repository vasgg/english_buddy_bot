from contextlib import suppress
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from database.crud.session import get_last_session_with_progress, get_session
from database.database_connector import DatabaseConnector
from sqlalchemy.exc import PendingRollbackError
from enums import SessionStatus

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from sqlalchemy.ext.asyncio import AsyncSession
    from database.models.session import Session


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
            data["db_session"] = db_session
            try:
                res = await handler(event, data)
            except Exception:
                with suppress(PendingRollbackError):
                    await db_session.rollback()
                raise
            else:
                with suppress(PendingRollbackError):
                    await db_session.commit()
                return res


class SessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        state: FSMContext = data["state"]
        state_data = await state.get_data()
        session_id = state_data.get("session_id")
        db_session: AsyncSession = data["db_session"]

        if session_id is not None:
            user_session = await get_session(session_id, db_session)
            if not user_session or user_session.status != SessionStatus.IN_PROGRESS:
                await self._handle_missing_session(event, state)
                return
        else:
            user_session = await self._recover_session_from_db(data, db_session, state)
            if not user_session:
                await self._handle_missing_session(event, state)
                return

        data["session"] = user_session
        return await handler(event, data)

    @staticmethod
    async def _recover_session_from_db(
        data: Dict[str, Any],
        db_session: "AsyncSession",
        state: "FSMContext",
    ) -> "Session | None":
        user = data.get("user")
        if not user:
            return None
        session = await get_last_session_with_progress(user.id, db_session)
        if session:
            await state.update_data(session_id=session.id)
        return session

    @staticmethod
    async def _handle_missing_session(event: Message | CallbackQuery, state: "FSMContext") -> None:
        await state.clear()
        message = "Не удалось найти активный урок. Начните урок заново через меню."
        if isinstance(event, CallbackQuery):
            with suppress(TelegramBadRequest):
                await event.answer(message)
            if event.message:
                await event.message.answer(message)
        else:
            await event.answer(message)
