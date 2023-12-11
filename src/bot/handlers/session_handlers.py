import asyncio

from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommandScopeChat
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.controllers.choice_controllers import get_random_answer
from bot.controllers.session_controller import get_wrong_answers_counter
from bot.controllers.slide_controllers import get_slide_by_id
from bot.database.models.session import Session
from bot.database.models.slide import Slide
from bot.database.models.user import User
from bot.handlers.lesson_handlers import common_processing
from bot.keyboards.callback_builders import HintCallbackFactory, QuizCallbackFactory, SlideCallbackFactory
from bot.keyboards.keyboards import get_hint_keyaboard
from bot.middlewares.session_middlewares import (
    SessionLogCallbackMiddleware,
    SessionLogMessageMiddleware,
    SessionMiddleware,
)
from bot.resources.answers import replies
from bot.resources.commands import special_commands
from bot.resources.enums import AnswerType, States

router = Router()
router.message.middleware.register(SessionMiddleware())
router.callback_query.middleware.register(SessionMiddleware())
router.message.middleware.register(SessionLogMessageMiddleware())
router.callback_query.middleware.register(SessionLogCallbackMiddleware())


@router.callback_query(SlideCallbackFactory.filter(), flags={"skip_session_logging": "true"})
async def slide_callback_processing(
    callback: types.CallbackQuery,
    bot: Bot,
    callback_data: SlideCallbackFactory,
    user: User,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    if callback.from_user.id in settings.ADMINS:
        await callback.bot.set_my_commands(special_commands, scope=BotCommandScopeChat(chat_id=callback.from_user.id))
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
    slide: Slide = await get_slide_by_id(lesson_id=lesson_id, slide_id=slide_id, db_session=db_session)
    data = await state.get_data()
    if "wrong_answer" in answer:
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=callback.from_user.id, message_id=data["quiz_options_msg_id"]
            )
        except KeyError:
            print("something went wrong")
        await callback.message.answer(text=await get_random_answer(mode=AnswerType.WRONG, db_session=db_session))
        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session)
        if wrong_answers_count >= 3:
            await callback.message.answer(
                text=replies["3_wrong_answers"].format(wrong_answers_count),
                reply_markup=get_hint_keyaboard(
                    session_id=session.id,
                    lesson_id=lesson_id,
                    slide_id=slide_id,
                    right_answer=slide.right_answers,
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
        )
    else:
        try:
            await callback.bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=data["quiz_options_msg_id"],
                text=slide.text.replace("…", f"<u>{slide.right_answers}</u>"),
            )
        except KeyError:
            print("something went wrong")
        await callback.message.answer(text=await get_random_answer(mode=AnswerType.RIGHT, db_session=db_session))
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
    answer = callback_data.answer
    slide: Slide = await get_slide_by_id(
        lesson_id=callback_data.lesson_id, slide_id=callback_data.slide_id, db_session=db_session
    )
    if answer == "show_hint":
        slide_id = slide.next_slide
        await callback.message.answer(text=replies["right_answer"].format(callback_data.right_answer))
        await asyncio.sleep(2)
    else:
        slide_id = callback_data.slide_id
    await callback.message.edit_reply_markup()
    await common_processing(
        bot=bot,
        user=user,
        lesson_id=callback_data.lesson_id,
        slide_id=slide_id,
        state=state,
        session=session,
        db_session=db_session,
    )
    await callback.answer()


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
    if input_word.startswith("/"):
        await state.set_state()
        return
    data = await state.get_data()
    lesson_id = data["quiz_word_lesson_id"]
    slide_id = data["quiz_word_slide_id"]
    slide: Slide = await get_slide_by_id(lesson_id=lesson_id, slide_id=slide_id, db_session=db_session)
    if input_word.lower() != slide.right_answers.lower():
        await message.answer(text=await get_random_answer(mode=AnswerType.WRONG, db_session=db_session))

        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session)
        if wrong_answers_count >= 3:
            await message.answer(
                text=replies["3_wrong_answers"].format(wrong_answers_count),
                reply_markup=get_hint_keyaboard(
                    session_id=session.id,
                    lesson_id=lesson_id,
                    slide_id=slide_id,
                    right_answer=slide.right_answers,
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
        await message.answer(text=await get_random_answer(mode=AnswerType.RIGHT, db_session=db_session))
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
    if input_phrase.startswith("/"):
        await state.set_state()
        return
    data = await state.get_data()
    lesson_id = data["quiz_phrase_lesson_id"]
    slide_id = data["quiz_phrase_slide_id"]
    slide: Slide = await get_slide_by_id(lesson_id=lesson_id, slide_id=slide_id, db_session=db_session)
    answers = slide.right_answers.split("|")
    answers_lower = [answer.lower() for answer in answers]
    almost_right_answers = slide.almost_right_answers.split("|")
    almost_right_answers_lower = [answer.lower() for answer in almost_right_answers]
    if input_phrase.lower() in answers_lower:
        await message.answer(text=await get_random_answer(mode=AnswerType.RIGHT, db_session=db_session))
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
        await message.answer(text=await get_random_answer(mode=AnswerType.WRONG, db_session=db_session))

        wrong_answers_count = await get_wrong_answers_counter(session.id, slide_id, db_session)
        if wrong_answers_count >= 3:
            await message.answer(
                text=replies["3_wrong_answers"].format(wrong_answers_count),
                reply_markup=get_hint_keyaboard(
                    session_id=session.id,
                    lesson_id=lesson_id,
                    slide_id=slide_id,
                    right_answer=slide.right_answers,
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
        )


@router.message(Command("position"), flags={"skip_session_logging": "true"})
async def set_slide_position(message: types.Message, state: FSMContext, session: Session) -> None:
    if not session:
        await message.answer(text="Please start session first")
        return
    await message.answer(text="Please enter target slide id")
    await state.set_state(States.INPUT_CUSTOM_SLIDE_ID)


@router.message(States.INPUT_CUSTOM_SLIDE_ID, flags={"skip_session_logging": "true"})
async def set_slide_position(message: types.Message, session: Session, db_session: AsyncSession) -> None:
    try:
        slide_id = int(message.text)
        current_session = session
        current_session.current_slide_id = slide_id
        await db_session.flush()
    except ValueError:
        await message.answer(text="Please provide correct slide id (integer)")
    # except Exception:
    #     await message.answer(text="Something went wrong. Please try again")
