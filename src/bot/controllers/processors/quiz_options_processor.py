import asyncio
from contextlib import suppress
import logging
from random import sample

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.processors.input_models import UserInputHint, UserInputMsg, UserQuizInput
from bot.controllers.processors.quiz_helpers import error_count_exceeded, show_hint_dialog
from bot.keyboards.keyboards import get_quiz_keyboard
from database.crud.answer import get_random_answer, get_text_by_prompt
from database.crud.quiz_answer import log_quiz_answer
from database.models.session import Session
from database.models.slide import Slide
from enums import ReactionType


async def show_quiz_options(
    event: types.Message,
    state: FSMContext,
    slide: Slide,
) -> bool:
    right_answer = slide.right_answers
    wrong_answers = slide.keyboard.split("|")
    elements = [right_answer, *wrong_answers]
    options = sample(population=elements, k=len(elements))
    markup = get_quiz_keyboard(words=options)
    msg = await event.answer(text=slide.text.replace("_", "…"), reply_markup=markup)
    await state.update_data(quiz_options_msg_id=msg.message_id)
    return False


async def response_options_correct(
    event: types.Message,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> None:
    try:
        with suppress(TelegramBadRequest):
            await event.edit_text(
                text=(
                    slide.text.replace("_", f"<u>{slide.right_answers}</u>")
                    if "_" in slide.text
                    else slide.text + '\nSystem message!\n\nВ тексте с вопросом к квизу "выбери правильный ответ" '
                    'всегда должен быть символ "_", чтобы при правильном ответе он подменялся на текст правильного '
                    "варианта."
                ),
            )
    except KeyError:
        logging.exception("something went wrong with quiz_options")
    await event.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
    await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)


async def response_options_wrong(
    event: types.Message,
    slide: Slide,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
    await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
    await show_quiz_options(event, state, slide)


async def process_quiz_options(
    event: types.Message,
    state: FSMContext,
    user_input: UserQuizInput,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    if not user_input:
        return await show_quiz_options(event, state, slide)
    match user_input:
        case UserInputHint() as hint_msg:
            with suppress(TelegramBadRequest):
                await event.delete_reply_markup()
            if hint_msg.hint_requested:
                await event.answer(
                    text=(await get_text_by_prompt(prompt="right_answer", db_session=db_session)).format(
                        slide.right_answers,
                    ),
                )
                await asyncio.sleep(2)
                return True
            else:
                return await show_quiz_options(event, state, slide)
        case UserInputMsg() as input_msg:
            if input_msg.text.lower() == slide.right_answers.lower():
                await response_options_correct(event, slide, session, db_session)
                return True
            await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
            if await error_count_exceeded(session.id, slide.id, db_session):
                await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
                await show_hint_dialog(event, db_session)
                return False
            await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
            await show_quiz_options(event, state, slide)
            return False
