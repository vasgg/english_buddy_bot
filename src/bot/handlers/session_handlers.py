import asyncio

from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.session_controller import (
    log_quiz_answer,
)
from bot.handlers.lesson_handlers import lesson_routine
from bot.keyboards.callback_data import HintCallbackFactory, QuizCallbackFactory, SlideCallbackFactory
from bot.keyboards.keyboards import get_hint_keyaboard
from bot.middlewares.session_middlewares import SessionMiddleware
from database.crud.answer import get_random_answer, get_text_by_prompt
from database.crud.session import get_wrong_answers_counter
from database.crud.slide import get_slide_by_id
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User
from enums import EventType, ReactionType, States

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

    # Сюда приходим только в том случае когда у текущего слайда нажата кнопка далее
    # перед вызовом надо крутануть стэп + 1
    #
    swow_slide(...)

    next_slide_id = session.next_slide_id
    await lesson_routine(
        bot=bot,
        user=user,
        slide_id=next_slide_id,
        state=state,
        session=session,
        db_session=db_session,
    )
    await callback.answer()


@router.callback_query(QuizCallbackFactory.filter())
async def quiz_callback_processing_new(
    callback: types.CallbackQuery,
    bot: Bot,
    callback_data: QuizCallbackFactory,
    user: User,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    user_input = UserInputMsg(text=callback_data.answer)
    swow_slide(...)


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
    path = session.get_path()
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
        await lesson_routine(
            bot=bot,
            user=user,
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
                text=slide.text.replace('…', f'<u>{slide.right_answers}</u>')
                if "…" in slide.text
                else slide.text + '\nSystem message!\n\nВ тексте с вопросом к квизу "выбери правильный ответ" '
                'всегда должен быть символ "…", чтобы при правильном ответе он подменялся на текст правильного варианта.',
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
        await lesson_routine(
            bot=bot,
            user=user,
            slide_id=path[path.index(slide.id) + 1],
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
    # сюда переносим функцию def handle_hint_input(msg, session):
    # тут я конструирую объект,  show_slide(UserInputHint(hint_requested=msg.data), session),
    # и вызываю фуннкцию шоу слайл (смотри scratch для примера)

    await callback.answer()
    # проверить в этом файле все функции, всю ли логику я уже переписал, если да, всё сношу. если нет, дописываю нужную логику
    slide: Slide = await get_slide_by_id(slide_id=callback_data.slide_id, db_session=db_session)
    slide_ids = [int(elem) for elem in session.path.split(".")]
    right_answer = slide.right_answers if '|' not in slide.right_answers else slide.right_answers.split('|')[0]
    if callback_data.payload == 'show_hint':
        slide_id = slide_ids[slide_ids.index(slide.id)]
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
        await lesson_routine(
            bot=bot,
            user=user,
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
    await lesson_routine(
        bot=bot,
        user=user,
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
    slide_ids = [int(elem) for elem in session.path.split(".")]
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
        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session) + 1
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
        await lesson_routine(
            bot=bot,
            user=user,
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
                text=slide.text.replace("…", f"<u>{slide.right_answers}</u>")
                if "…" in slide.text
                else slide.text + '\nSystem message!\n\nВ тексте с вопросом к квизу "впиши слово" '
                'всегда должен быть символ "…", чтобы при правильном ответе он подменялся на текст правильного варианта.',
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
        await lesson_routine(
            bot=bot,
            user=user,
            slide_id=slide_ids[slide_ids.index(slide.id) + 1],
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
    # TODO: тут вызываем функцию handle_user_input
    # переносим всю логику ниже в эту функцию
    input_phrase = message.text
    data = await state.get_data()
    lesson_id = data["quiz_phrase_lesson_id"]
    slide_id = data["quiz_phrase_slide_id"]
    slide: Slide = await get_slide_by_id(slide_id=slide_id, db_session=db_session)
    path = [int(elem) for elem in session.path.split(".")]
    try:
        next_slide_id = path[path.index(slide.id) + 1]
    except IndexError:
        next_slide_id = session.current_slide_id
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
        await lesson_routine(
            bot=bot,
            user=user,
            slide_id=next_slide_id,
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
        await lesson_routine(
            bot=bot,
            user=user,
            slide_id=next_slide_id,
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
        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session) + 1
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
        await lesson_routine(
            bot=bot,
            user=user,
            slide_id=slide_id,
            state=state,
            session=session,
            db_session=db_session,
            skip_step_increment=True,
        )
