import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.final_controllers import finish_session
from bot.controllers.processors.input_models import UserInputHint, UserInputMsg
from bot.controllers.slide_controllers import show_slides
from bot.controllers.user_controllers import show_start_menu
from bot.keyboards.callback_data import (
    ExtraSlidesCallbackFactory,
    HintCallbackFactory,
    QuizCallbackFactory,
)
from bot.middlewares.session_middlewares import SessionMiddleware
from database.models.session import Session
from enums import States

logger = logging.Logger(__name__)

router = Router()
router.message.middleware.register(SessionMiddleware())
router.callback_query.middleware.register(SessionMiddleware())


@router.callback_query(F.data == 'further_button')
async def further_button_callback_processing(
        callback: types.CallbackQuery,
        state: FSMContext,
        session: Session,
        db_session: AsyncSession,
) -> None:
    await callback.answer()
    await callback.message.delete_reply_markup()
    session.current_step += 1
    await show_slides(callback.message, state, session, db_session)


@router.callback_query(QuizCallbackFactory.filter())
async def quiz_callback_processing(
        callback: types.CallbackQuery,
        callback_data: QuizCallbackFactory,
        state: FSMContext,
        session: Session,
        db_session: AsyncSession,
) -> None:
    await callback.message.delete_reply_markup()
    user_input = UserInputMsg(text=callback_data.answer)
    await show_slides(callback.message, state, session, db_session, user_input)
    await callback.answer()


@router.callback_query(HintCallbackFactory.filter())
async def hint_callback(
        callback: types.CallbackQuery,
        callback_data: HintCallbackFactory,
        state: FSMContext,
        session: Session,
        db_session: AsyncSession,
) -> None:
    user_input = UserInputHint(hint_requested=callback_data.hint_requested)
    await show_slides(callback.message, state, session, db_session, user_input)
    await callback.answer()


@router.message(States.INPUT_PHRASE)
@router.message(States.INPUT_WORD)
async def check_input_word(
        message: types.Message,
        state: FSMContext,
        session: Session,
        db_session: AsyncSession,
) -> None:
    user_input = UserInputMsg(text=message.text)
    await show_slides(message, state, session, db_session, user_input)


@router.callback_query(ExtraSlidesCallbackFactory.filter())
async def handle_extra_slide_answer(
        callback: types.CallbackQuery,
        callback_data: ExtraSlidesCallbackFactory,
        state: FSMContext,
        session: Session,
        db_session: AsyncSession,
) -> None:
    await callback.message.delete_reply_markup()
    if callback_data.extra_slides_requested:
        session.set_extra()
        await show_slides(callback.message, state, session, db_session)
    else:
        await finish_session(session, db_session)
        await show_start_menu(callback.message, session.user_id, db_session)
        await state.clear()
        return
