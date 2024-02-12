import asyncio

from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.answer_controllers import get_random_answer, get_text_by_prompt
from bot.controllers.session_controller import (
    get_wrong_answers_counter,
    log_quiz_answer,
)
from bot.controllers.slide_controllers import get_slide_by_id
from bot.handlers.lesson_handlers import common_processing
from bot.keyboards.callback_builders import HintCallbackFactory, QuizCallbackFactory, SlideCallbackFactory
from bot.keyboards.keyboards import get_hint_keyaboard
from bot.middlewares.session_middlewares import SessionMiddleware
from bot.resources.enums import EventType, ReactionType, States
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User

router = Router()
router.message.middleware.register(SessionMiddleware())
router.callback_query.middleware.register(SessionMiddleware())


@router.callback_query(SlideCallbackFactory.filter())
async def slide_callback_processing(
    callback: types.CallbackQuery,
    bot: Bot,
    callback_data: SlideCallbackFactory,
    user: User,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    await callback.message.delete_reply_markup()
    lesson_id = callback_data.lesson_id
    next_slide_id = callback_data.next_slide_id
    await common_processing(
        bot=bot,
        user=user,
        lesson_id=lesson_id,
        slide_id=next_slide_id,
        state=state,
        session=session,
        db_session=db_session,
    )
    await callback.answer()


@router.callback_query(QuizCallbackFactory.filter())
async def quiz_callback_processing(
    callback: types.CallbackQuery,
    bot: Bot,
    callback_data: QuizCallbackFactory,
    user: User,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    lesson_id = callback_data.lesson_id
    slide_id = callback_data.slide_id
    answer = callback_data.answer
    slide: Slide = await get_slide_by_id(slide_id=slide_id, db_session=db_session)
    data = await state.get_data()
    if 'wrong_answer' in answer:
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=callback.from_user.id, message_id=data['quiz_options_msg_id']
            )
        except KeyError:
            print('something went wrong')
        await callback.message.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
        await log_quiz_answer(
            session=session,
            mode=EventType.CALLBACK_QUERY,
            event=callback,
            is_correct=False,
            slide=slide,
            db_session=db_session,
        )
        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session)
        if wrong_answers_count >= 3:
            await callback.message.answer(
                text=(await get_text_by_prompt(prompt='3_wrong_answers', db_session=db_session)).format(
                    wrong_answers_count
                ),
                reply_markup=get_hint_keyaboard(
                    lesson_id=lesson_id,
                    slide_id=slide_id,
                ),
            )
            return
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=lesson_id,
            slide_id=slide_id,
            state=state,
            session=session,
            db_session=db_session,
            skip_step_increment=True,
        )
    else:
        try:
            await callback.bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=data['quiz_options_msg_id'],
                text=slide.text.replace('…', f'<u>{slide.right_answers}</u>'),
            )
        except KeyError:
            print('something went wrong')
        await callback.message.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
        await log_quiz_answer(
            session=session,
            mode=EventType.CALLBACK_QUERY,
            event=callback,
            is_correct=True,
            slide=slide,
            db_session=db_session,
        )
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=lesson_id,
            slide_id=slide.next_slide,
            state=state,
            session=session,
            db_session=db_session,
        )
    await callback.answer()


@router.callback_query(HintCallbackFactory.filter())
async def hint_callback(
    callback: types.CallbackQuery,
    bot: Bot,
    callback_data: HintCallbackFactory,
    user: User,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    await callback.answer()
    slide: Slide = await get_slide_by_id(slide_id=callback_data.slide_id, db_session=db_session)
    right_answer = slide.right_answers if '|' not in slide.right_answers else slide.right_answers.split('|')[0]
    if callback_data.payload == 'show_hint':
        slide_id = slide.next_slide
        await callback.message.answer(
            text=(await get_text_by_prompt(prompt='right_answer', db_session=db_session)).format(right_answer)
        )
        await log_quiz_answer(
            session=session,
            mode=EventType.HINT,
            event=callback,
            is_correct=None,
            slide=slide,
            db_session=db_session,
        )
        await asyncio.sleep(2)
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=callback_data.lesson_id,
            slide_id=slide_id,
            state=state,
            session=session,
            db_session=db_session,
        )
        return
    else:
        slide_id = callback_data.slide_id
    await callback.message.edit_reply_markup()
    await log_quiz_answer(
        session=session,
        mode=EventType.CONTINUE,
        event=callback,
        # event=callback_data,
        is_correct=None,
        slide=slide,
        db_session=db_session,
    )
    await common_processing(
        bot=bot,
        user=user,
        lesson_id=callback_data.lesson_id,
        slide_id=slide_id,
        state=state,
        session=session,
        db_session=db_session,
        skip_step_increment=True,
    )


@router.message(States.INPUT_WORD)
async def check_input_word(
    message: types.Message,
    bot: Bot,
    user: User,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    input_word = message.text
    data = await state.get_data()
    lesson_id = data['quiz_word_lesson_id']
    slide_id = data['quiz_word_slide_id']
    slide: Slide = await get_slide_by_id(slide_id=slide_id, db_session=db_session)
    if input_word.lower() != slide.right_answers.lower():
        await message.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
        await log_quiz_answer(
            session=session,
            mode=EventType.MESSAGE,
            event=message,
            is_correct=False,
            slide=slide,
            db_session=db_session,
        )
        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session)
        if wrong_answers_count >= 3:
            await message.answer(
                text=(await get_text_by_prompt(prompt='3_wrong_answers', db_session=db_session)).format(
                    wrong_answers_count
                ),
                reply_markup=get_hint_keyaboard(
                    lesson_id=lesson_id,
                    slide_id=slide_id,
                ),
            )
            return
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=lesson_id,
            slide_id=slide_id,
            state=state,
            session=session,
            db_session=db_session,
            skip_step_increment=True,
        )
    else:
        try:
            await bot.edit_message_text(
                chat_id=message.from_user.id,
                message_id=data["quiz_word_msg_id"],
                text=slide.text.replace("…", f"<u>{slide.right_answers}</u>"),
            )
        except KeyError:
            print("something went wrong")
        await message.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
        await log_quiz_answer(
            session=session,
            mode=EventType.MESSAGE,
            event=message,
            is_correct=True,
            slide=slide,
            db_session=db_session,
        )
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=lesson_id,
            slide_id=slide.next_slide,
            state=state,
            session=session,
            db_session=db_session,
        )


@router.message(States.INPUT_PHRASE)
async def check_input_phrase(
    message: types.Message,
    bot: Bot,
    user: User,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    input_phrase = message.text
    data = await state.get_data()
    lesson_id = data["quiz_phrase_lesson_id"]
    slide_id = data["quiz_phrase_slide_id"]
    slide: Slide = await get_slide_by_id(slide_id=slide_id, db_session=db_session)
    answers = slide.right_answers.split("|")
    answers_lower = [answer.lower() for answer in answers]
    almost_right_answers = slide.almost_right_answers.split("|")
    almost_right_answers_lower = [answer.lower() for answer in almost_right_answers]
    if input_phrase.lower() in answers_lower:
        await message.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
        await log_quiz_answer(
            session=session,
            mode=EventType.MESSAGE,
            event=message,
            is_correct=True,
            slide=slide,
            db_session=db_session,
        )
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=lesson_id,
            slide_id=slide.next_slide,
            state=state,
            session=session,
            db_session=db_session,
        )
    elif input_phrase.lower() in almost_right_answers_lower:
        await message.answer(text=slide.almost_right_answer_reply)
        await log_quiz_answer(
            session=session,
            mode=EventType.MESSAGE,
            event=message,
            is_correct=True,
            slide=slide,
            db_session=db_session,
        )
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=lesson_id,
            slide_id=slide.next_slide,
            state=state,
            session=session,
            db_session=db_session,
        )
    else:
        await message.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
        await log_quiz_answer(
            session=session,
            mode=EventType.MESSAGE,
            event=message,
            is_correct=False,
            slide=slide,
            db_session=db_session,
        )
        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session)
        if wrong_answers_count >= 3:
            await message.answer(
                text=(await get_text_by_prompt(prompt='3_wrong_answers', db_session=db_session)).format(
                    wrong_answers_count
                ),
                reply_markup=get_hint_keyaboard(
                    lesson_id=lesson_id,
                    slide_id=slide_id,
                ),
            )
            return
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=lesson_id,
            slide_id=slide_id,
            state=state,
            session=session,
            db_session=db_session,
            skip_step_increment=True,
        )
