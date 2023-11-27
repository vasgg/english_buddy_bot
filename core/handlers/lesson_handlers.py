from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import get_lesson_slide_amount, lesson_routine
from core.controllers.slide_controllers import get_slide
from core.controllers.user_controllers import get_user_progress
from core.database.models import User
from core.keyboards.callback_builders import LessonsCallbackFactory, QuizCallbackFactory, SlideCallbackFactory
from core.resources.enums import States

router = Router()


async def common_processing(bot: Bot, user: User, lesson_number: int, slide_number: int,
                            state: FSMContext, session: AsyncSession) -> None:
    progress = await get_user_progress(user_id=user.id, lesson_number=lesson_number, slide_number=slide_number, session=session)
    slide_amount = await get_lesson_slide_amount(lesson_number=lesson_number, session=session)
    await lesson_routine(bot=bot, user=user, lesson_number=lesson_number, current_slide=progress, slide_amount=slide_amount,
                         state=state, session=session)


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(callback: types.CallbackQuery, bot: Bot, callback_data: LessonsCallbackFactory, user: User,
                                     state: FSMContext, session: AsyncSession) -> None:
    await common_processing(bot=bot, user=user, lesson_number=callback_data.lesson_number, slide_number=1,
                            state=state, session=session)
    await callback.answer()


@router.callback_query(SlideCallbackFactory.filter())
async def slide_callback_processing(callback: types.CallbackQuery, bot: Bot, callback_data: SlideCallbackFactory, user: User,
                                    state: FSMContext, session: AsyncSession) -> None:
    lesson_number = callback_data.lesson_number
    slide_number = callback_data.slide_number
    await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number,
                            state=state, session=session)
    await callback.answer()


@router.callback_query(QuizCallbackFactory.filter())
async def quiz_callback_processing(callback: types.CallbackQuery, bot: Bot, callback_data: QuizCallbackFactory, user: User,
                                   state: FSMContext, session: AsyncSession) -> None:
    lesson_number = callback_data.lesson_number
    slide_number = callback_data.slide_number
    answer = callback_data.answer
    slide = await get_slide(lesson_number=lesson_number, slide_number=slide_number, session=session)
    data = await state.get_data()
    if answer == 'wrong':
        try:
            await callback.bot.edit_message_reply_markup(chat_id=callback.from_user.id,
                                                         message_id=data['quiz_options_msg_id'])
        except KeyError:
            print('something went wrong')
        await callback.message.answer(text=slide.wrong_answer_reply)
        await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number,
                                state=state, session=session)
    else:
        try:
            await callback.bot.edit_message_text(chat_id=callback.from_user.id,
                                                 message_id=data['quiz_options_msg_id'],
                                                 text=slide.text.replace('…', f'<u>{slide.right_answers}</u>'))
        except KeyError:
            print('something went wrong')
        await callback.message.answer(text=slide.right_answer_reply)
        await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number + 1,
                                state=state, session=session)
    await callback.answer()


@router.message(States.INPUT_WORD)
async def check_input_word(message: types.Message, bot: Bot, user: User, state: FSMContext, session: AsyncSession) -> None:
    input_word = message.text
    data = await state.get_data()
    lesson_number = data['quiz_word_lesson_number']
    slide_number = data['quiz_word_slide_number']
    slide = await get_slide(lesson_number=lesson_number, slide_number=slide_number, session=session)
    if input_word.lower() != slide.right_answers.lower():
        await message.answer(text=slide.wrong_answer_reply)
        await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number,
                                state=state, session=session)
    else:
        try:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=data['quiz_word_msg_id'],
                                        text=slide.text.replace('…', f'<u>{slide.right_answers}</u>'))
        except KeyError:
            print('something went wrong')
        await message.answer(text=slide.right_answer_reply)
        await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number + 1,
                                state=state, session=session)


@router.message(States.INPUT_PHRASE)
async def check_input_phrase(message: types.Message, bot: Bot, user: User, state: FSMContext, session: AsyncSession) -> None:
    input_phrase = message.text
    data = await state.get_data()
    lesson_number = data['quiz_phrase_lesson_number']
    slide_number = data['quiz_phrase_slide_number']
    slide = await get_slide(lesson_number=lesson_number, slide_number=slide_number, session=session)
    answers = slide.right_answers.split('|')
    answers_lower = [answer.lower() for answer in answers]
    almost_right_answers = slide.almost_right_answers.split('|')
    almost_right_answers_lower = [answer.lower() for answer in almost_right_answers]
    if input_phrase.lower() in answers_lower:
        await message.answer(text=slide.right_answer_reply)
        await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number + 1,
                                state=state, session=session)
    elif input_phrase.lower() in almost_right_answers_lower:
        await message.answer(text=slide.almost_right_answer_reply)
        await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number + 1,
                                state=state, session=session)
    else:
        await message.answer(text=slide.wrong_answer_reply)
        await common_processing(bot=bot, user=user, lesson_number=lesson_number, slide_number=slide_number,
                                state=state, session=session)
