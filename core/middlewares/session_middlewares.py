from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.session_controller import get_session
from core.controllers.slide_controllers import get_slide_by_id
from core.database.db import db
from core.database.models import Session, SessionLog, Slide


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with db.session_factory() as db_session:
            data["db_session"] = db_session
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
        state: FSMContext = data["state"]
        state_data = await state.get_data()
        session_id = state_data["session_id"]
        db_session: AsyncSession = data["db_session"]
        user_session = await get_session(session_id, db_session)
        data["session"] = user_session
        res = await handler(event, data)
        return res


class SessionLogMessageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        db_session: AsyncSession = data["db_session"]
        session: Session = data["session"]
        slide: Slide = await get_slide_by_id(
            lesson_id=session.lesson_id,
            slide_id=session.current_slide_id,
            db_session=db_session,
        )
        json_event = event.model_dump_json(exclude_unset=True)
        session_log = SessionLog(
            session_id=session.id,
            slide_id=session.current_slide_id,
            slide_type=slide.slide_type,
            data=event.text,
            update=json_event,
        )
        db_session.add(session_log)
        return await handler(event, data)


class SessionLogCallbackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        # todo: refactor as above
        state: FSMContext = data["state"]
        state_data = await state.get_data()
        session_id = state_data["session_id"]
        callback_data = data["callback_data"]
        db_session: AsyncSession = data["db_session"]
        session = await get_session(session_id, db_session)
        answer = getattr(callback_data, "answer", None)
        slide: Slide = await get_slide_by_id(
            lesson_id=session.lesson_id,
            slide_id=session.current_slide_id,
            db_session=db_session,
        )
        json_event = event.model_dump_json(exclude_unset=True)
        session_log = SessionLog(
            session_id=session_id,
            slide_id=session.current_slide_id,
            slide_type=slide.slide_type,
            data=answer,
            update=json_event,
        )
        db_session.add(session_log)
        return await handler(event, data)
