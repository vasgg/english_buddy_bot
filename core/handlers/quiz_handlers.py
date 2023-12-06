from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.choice_controllers import get_random_answer
from core.controllers.slide_controllers import get_slide_by_id
from core.database.models import User
from core.handlers.lesson_handlers import common_processing
from core.keyboards.callback_builders import QuizCallbackFactory
from core.resources.enums import AnswerType, States

router = Router()


@router.callback_query(QuizCallbackFactory.filter())
async def quiz_callback_processing(callback: types.CallbackQuery, bot: Bot, callback_data: QuizCallbackFactory, user: User,
                                   state: FSMContext, session: AsyncSession) -> None:
    lesson_id = callback_data.lesson_id
    slide_id = callback_data.slide_id
    answer = callback_data.answer
    slide = await get_slide_by_id(lesson_id=lesson_id, slide_id=slide_id, session=session)
    data = await state.get_data()
    if answer == 'wrong':
        try:
            await callback.bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=data['quiz_options_msg_id'])
        except KeyError:
            print('something went wrong')
        await callback.message.answer(text=await get_random_answer(mode=AnswerType.WRONG, session=session))
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id, state=state, session=session)
    else:
        try:
            await callback.bot.edit_message_text(chat_id=callback.from_user.id,
                                                 message_id=data['quiz_options_msg_id'],
                                                 text=slide.text.replace('…', f'<u>{slide.right_answers}</u>'))
        except KeyError:
            print('something went wrong')
        await callback.message.answer(text=await get_random_answer(mode=AnswerType.RIGHT, session=session))
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide, state=state, session=session)
    await callback.answer()


@router.message(States.INPUT_WORD)
async def check_input_word(message: types.Message, bot: Bot, user: User, state: FSMContext, session: AsyncSession) -> None:
    input_word = message.text
    data = await state.get_data()
    lesson_id = data['quiz_word_lesson_id']
    slide_id = data['quiz_word_slide_id']
    slide = await get_slide_by_id(lesson_id=lesson_id, slide_id=slide_id, session=session)
    if input_word.lower() != slide.right_answers.lower():
        await message.answer(text=await get_random_answer(mode=AnswerType.WRONG, session=session))
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id,
                                state=state, session=session)
    else:
        try:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=data['quiz_word_msg_id'],
                                        text=slide.text.replace('…', f'<u>{slide.right_answers}</u>'))
        except KeyError:
            print('something went wrong')
        await message.answer(text=await get_random_answer(mode=AnswerType.RIGHT, session=session))
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide,
                                state=state, session=session)


@router.message(States.INPUT_PHRASE)
async def check_input_phrase(message: types.Message, bot: Bot, user: User, state: FSMContext, session: AsyncSession) -> None:
    input_phrase = message.text
    data = await state.get_data()
    lesson_id = data['quiz_phrase_lesson_id']
    slide_id = data['quiz_phrase_slide_id']
    slide = await get_slide_by_id(lesson_id=lesson_id, slide_id=slide_id, session=session)
    answers = slide.right_answers.split('|')
    answers_lower = [answer.lower() for answer in answers]
    almost_right_answers = slide.almost_right_answers.split('|')
    almost_right_answers_lower = [answer.lower() for answer in almost_right_answers]
    if input_phrase.lower() in answers_lower:
        await message.answer(text=await get_random_answer(mode=AnswerType.RIGHT, session=session))
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide, state=state, session=session)
    elif input_phrase.lower() in almost_right_answers_lower:
        await message.answer(text=slide.almost_right_answer_reply)
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide, state=state, session=session)
    else:
        await message.answer(text=await get_random_answer(mode=AnswerType.WRONG, session=session))
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id,
                                state=state, session=session)
