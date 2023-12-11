from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import PendingRollbackError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.session_controller import get_session
from bot.database.db import db


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with db.session_factory() as db_session:
            # TODO: mb change to db_session factory
            data["db_session"] = db_session
            res = await handler(event, data)
            # TODO: probably,check how session handles it
            # check how commit behaves
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
        skip_session_logging = get_flag(data, "skip_session_logging")
        if skip_session_logging:
            return await handler(event, data)
        # db_session: AsyncSession = data["db_session"]
        # session: Session = data["session"]
        # slide: Slide = await get_slide_by_id(
        #     lesson_id=session.lesson_id,
        #     slide_id=session.current_slide_id,
        #     db_session=db_session,
        # )
        # if slide.slide_type == SlideType.QUIZ_INPUT_PHRASE:
        #     answers = slide.right_answers.split("|")
        #     answers_lower = [answer.lower() for answer in answers]
        #     almost_right_answers = slide.almost_right_answers.split("|")
        #     almost_right_answers_lower = [answer.lower() for answer in almost_right_answers]
        #     is_correct = (
        #         True
        #         if event.text.lower() in answers_lower or event.text.lower() in almost_right_answers_lower
        #         else False
        #     )
        # else:
        #     if event.text in ["continue_button", "show_hint", "/start", "/position", None]:
        #         is_correct = None
        #     else:
        #         is_correct = True
        # json_event = event.model_dump_json(exclude_unset=True)
        # # noinspection PyUnboundLocalVariable
        # session_log = SessionLog(
        #     session_id=session.id,
        #     slide_id=session.current_slide_id,
        #     slide_type=slide.slide_type,
        #     data=event.text,
        #     is_correct=is_correct,
        #     update=json_event,
        # )
        # db_session.add(session_log)
        return await handler(event, data)


class SessionLogCallbackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        skip_session_logging = get_flag(data, "skip_session_logging")
        if skip_session_logging:
            return await handler(event, data)
        # db_session: AsyncSession = data["db_session"]
        # session: Session = data["session"]
        # answer = getattr(data["callback_data"], "answer", None)
        # slide: Slide = await get_slide_by_id(
        #     lesson_id=session.lesson_id,
        #     slide_id=session.current_slide_id,
        #     db_session=db_session,
        # )
        # if slide.slide_type == SlideType.QUIZ_INPUT_PHRASE:
        #     right_answers = slide.right_answers.split("|")
        #     almost_right_answers = slide.almost_right_answers.split("|")
        #     is_correct = True if answer in right_answers or answer in almost_right_answers else False
        # if answer in ["continue_button", "show_hint", "/start", "/position", None]:
        #     is_correct = None
        # else:
        #     is_correct = True
        # # is_correct = True if answer == slide.right_answers else False
        # json_event = event.model_dump_json(exclude_unset=True)
        # # noinspection PyUnboundLocalVariable
        # session_log = SessionLog(
        #     session_id=session.id,
        #     slide_id=session.current_slide_id,
        #     slide_type=slide.slide_type,
        #     data=answer,
        #     is_correct=is_correct,
        #     update=json_event,
        # )
        # db_session.add(session_log)
        return await handler(event, data)
