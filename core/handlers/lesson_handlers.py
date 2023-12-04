from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import lesson_routine
from core.controllers.slide_controllers import get_slide_by_id
from core.controllers.user_controllers import get_lesson_progress, update_user_progress
from core.database.models import User
from core.keyboards.callback_builders import LessonStartFromCallbackFactory, LessonsCallbackFactory, QuizCallbackFactory, SlideCallbackFactory
from core.keyboards.keyboards import get_lesson_progress_keyboard
from core.resources.enums import States, UserLessonProgress

router = Router()


async def common_processing(bot: Bot, user: User, lesson_id: int, slide_id: int, state: FSMContext, session: AsyncSession) -> None:
    await update_user_progress(user_id=user.id, lesson_id=lesson_id, current_slide=slide_id, session=session)
    await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id, state=state, session=session)


@router.callback_query(LessonsCallbackFactory.filter())
async def lesson_callback_processing(callback: types.CallbackQuery, callback_data: LessonsCallbackFactory, user: User,
                                     state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=data['start_msg_id'])
    progress = await get_lesson_progress(user_id=user.id, lesson_id=callback_data.lesson_id, session=session)
    if not progress:
        msg = await callback.message.answer(text='Вы можете начать урок сначала, или сразу перейти к экзамену.',
                                            reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.NO_PROGRESS,
                                                                                            lesson_id=callback_data.lesson_id, session=session))
    else:
        msg = await callback.message.answer(text='Вы можете продолжить урок, или начать его сначала.',
                                            reply_markup=await get_lesson_progress_keyboard(mode=UserLessonProgress.IN_PROGRESS,
                                                                                            lesson_id=callback_data.lesson_id,
                                                                                            current_slide=progress,
                                                                                            session=session))
    await state.update_data(start_from_msg_id=msg.message_id)
    await callback.answer()


@router.callback_query(LessonStartFromCallbackFactory.filter())
async def lesson_start_from_callback_processing(callback: types.CallbackQuery, callback_data: LessonStartFromCallbackFactory,
                                                bot: Bot, user: User, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=data['start_from_msg_id'])
    lesson_id = callback_data.lesson_id
    slide_id = callback_data.slide_id
    if not slide_id:
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=1, state=state, session=session)
    else:
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id, state=state, session=session)
    await callback.answer()


@router.callback_query(SlideCallbackFactory.filter())
async def slide_callback_processing(callback: types.CallbackQuery, bot: Bot, callback_data: SlideCallbackFactory, user: User,
                                    state: FSMContext, session: AsyncSession) -> None:
    lesson_id = callback_data.lesson_id
    next_slide_id = callback_data.next_slide_id
    await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=next_slide_id, state=state, session=session)
    await callback.answer()


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
        await callback.message.answer(text=slide.wrong_answer_reply)
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id, state=state, session=session)
    else:
        try:
            await callback.bot.edit_message_text(chat_id=callback.from_user.id,
                                                 message_id=data['quiz_options_msg_id'],
                                                 text=slide.text.replace('…', f'<u>{slide.right_answers}</u>'))
        except KeyError:
            print('something went wrong')
        await callback.message.answer(text=slide.right_answer_reply)
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
        await message.answer(text=slide.wrong_answer_reply)
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id,
                                state=state, session=session)
    else:
        try:
            await bot.edit_message_text(chat_id=message.from_user.id,
                                        message_id=data['quiz_word_msg_id'],
                                        text=slide.text.replace('…', f'<u>{slide.right_answers}</u>'))
        except KeyError:
            print('something went wrong')
        await message.answer(text=slide.right_answer_reply)
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
        await message.answer(text=slide.right_answer_reply)
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide, state=state, session=session)
    elif input_phrase.lower() in almost_right_answers_lower:
        await message.answer(text=slide.almost_right_answer_reply)
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide, state=state, session=session)
    else:
        await message.answer(text=slide.wrong_answer_reply)
        await common_processing(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide_id,
                                state=state, session=session)
