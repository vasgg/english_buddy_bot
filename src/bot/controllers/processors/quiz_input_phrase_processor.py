import asyncio

from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.controllers.processors.input_models import UserInputHint, UserInputMsg, UserQuizInput
from bot.controllers.processors.quiz_helpers import error_count_exceeded, show_hint_dialog
from database.crud.answer import get_random_answer, get_text_by_prompt
from database.crud.quiz_answer import log_quiz_answer
from database.models.session import Session
from database.models.slide import Slide
from enums import ReactionType, States
from sqlalchemy.ext.asyncio import AsyncSession


async def show_quiz_input_phrase(
    event: types.Message,
    state: FSMContext,
    slide: Slide,
) -> bool:
    msg = await event.answer(text=slide.text)
    await state.update_data(quiz_phrase_msg_id=msg.message_id)
    await state.set_state(States.INPUT_PHRASE)
    return False


async def process_quiz_input_phrase(
    event: types.Message,
    state: FSMContext,
    user_input: UserQuizInput,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    if not user_input:
        return await show_quiz_input_phrase(event, state, slide)
    match user_input:
        case UserInputHint() as hint_msg:
            if hint_msg.hint_requested:
                await event.answer(
                    text=(await get_text_by_prompt(prompt='right_answer', db_session=db_session)).format(
                        slide.right_answers if '|' not in slide.right_answers else slide.right_answers.split('|')[0],
                    ),
                )
                await asyncio.sleep(2)
                return True
            else:
                return await show_quiz_input_phrase(event, state, slide)
        case UserInputMsg() as input_msg:
            answers_lower = [answer.lower() for answer in slide.right_answers.split("|")]
            almost_right_answers_lower = [answer.lower() for answer in slide.almost_right_answers.split("|")]
            if input_msg.text.lower() in answers_lower:
                await event.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
                await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)
                return True
            elif input_msg.text.lower() in almost_right_answers_lower:
                await event.answer(text=slide.almost_right_answer_reply)
                await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)
                return True

            # Handling wrong answers below

            await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
            await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))

            if error_count_exceeded(session.id, slide.id, db_session):
                await show_hint_dialog(event, db_session)
                return False

            await show_quiz_input_phrase(event, state, slide)

            return False
