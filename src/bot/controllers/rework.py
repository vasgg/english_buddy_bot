import asyncio
from pathlib import Path
from random import sample

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.session_controller import log_quiz_answer
from bot.controllers.user_controllers import show_start_menu
from bot.keyboards.keyboards import get_furher_button, get_quiz_keyboard
from database.crud.answer import get_random_answer, get_random_sticker_id
from database.crud.session import get_wrong_answers_counter
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User
from enums import EventType, KeyboardType, ReactionType, SlideType, States, StickerType


class UserInput(BaseModel):
    answer_option: str | None = None
    answer_word: str | None = None
    answer_phrase: str | None = None
    further_button: bool | None = None
    hint_button: bool | None = None
    extra_button: bool | None = None


async def handle_text(
    user: User,
    bot: Bot,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    markup = None
    if slide.keyboard_type == KeyboardType.FURTHER:
        markup = (
            get_furher_button()
        )  # тут надо знать айди следующего слайда. это надо тут смотреть, или вынести эту логику в саму клавиатуру? или вообще переделать?

    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    await bot.send_message(
        chat_id=user.telegram_id,
        text=slide.text,
        reply_markup=markup,
    )
    if slide.keyboard_type == KeyboardType.FURTHER:
        return False
    return True


async def handle_image(
    user: User,
    bot: Bot,
    slide: Slide,
    session: Session,
) -> bool:
    markup = None
    image_path = Path(f'src/webapp/static/lessons_images/{session.lesson_id}/{slide.picture}')
    if not image_path.exists():
        image_path = Path(f'src/webapp/static/lessons_images/Image_not_available.png')
    if slide.keyboard_type == KeyboardType.FURTHER:
        markup = (
            get_furher_button()
        )  # тут надо знать айди следующего слайда. это надо тут смотреть, или вынести эту логику в саму клавиатуру?
    await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=image_path), reply_markup=markup)
    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    if slide.keyboard_type == KeyboardType.FURTHER:
        return False
    return True


async def handle_sticker(
    user: User,
    bot: Bot,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    sticker_type = StickerType.SMALL if slide.slide_type == SlideType.SMALL_STICKER else StickerType.BIG
    await bot.send_sticker(
        chat_id=user.telegram_id, sticker=await get_random_sticker_id(mode=sticker_type, db_session=db_session)
    )

    # return False  # а тут я не понял, как это должно работать
    return True


async def handle_dict(
    user: User,
    bot: Bot,
    slide: Slide,
    session: Session,
) -> bool:
    msg = await bot.send_message(chat_id=user.telegram_id, text=slide.text)
    await bot.pin_chat_message(
        chat_id=user.telegram_id,
        message_id=msg.message_id,
        disable_notification=True,
    )
    # return False  # а тут я не понял, как это должно работать
    return True


async def show_quiz(
    user: User,
    bot: Bot,
    state: FSMContext,
    slide: Slide,
    session: Session,
) -> bool:
    match slide.slide_type:
        case SlideType.QUIZ_OPTIONS:
            right_answer = slide.right_answers
            wrong_answers = slide.keyboard.split('|')
            elements = [right_answer, *wrong_answers]
            options = sample(population=elements, k=len(elements))
            markup = get_quiz_keyboard(
                words=options, answer=right_answer, lesson_id=session.lesson_id, slide_id=slide.id
            )
            msg = await bot.send_message(chat_id=user.telegram_id, text=slide.text, reply_markup=markup)
            await state.update_data(quiz_options_msg_id=msg.message_id)
            return False  # я правильно понял задумку?
        case SlideType.QUIZ_INPUT_WORD | SlideType.QUIZ_INPUT_PHRASE:
            msg = await bot.send_message(chat_id=user.telegram_id, text=slide.text)
            if slide.slide_type == SlideType.QUIZ_INPUT_WORD:
                await state.update_data(
                    quiz_word_msg_id=msg.message_id,
                    quiz_word_lesson_id=session.lesson_id,
                    quiz_word_slide_id=slide.id,
                )
                state_ = States.INPUT_WORD
            else:
                await state.update_data(
                    quiz_phrase_msg_id=msg.message_id,
                    quiz_phrase_lesson_id=session.lesson_id,
                    quiz_phrase_slide_id=slide.id,
                )
                state_ = States.INPUT_PHRASE
            await state.set_state(state_)
            return False  # я правильно понял задумку?
        case _:
            assert False, f'Unexpected slide type: {slide.slide_type}'
    #     а тут надо флаг задать? и какой?


async def error_count_exceeded(session_id: int, slide_id: int, db_session: AsyncSession) -> bool:
    wrong_answers_count = (
        await get_wrong_answers_counter(session_id, slide_id, db_session) + 1
    )  # раньше считало норм, потом сломалось. WTF?
    if wrong_answers_count >= 3:
        return True
    return False


async def response_correct(  # каллбэк сюда кидаем, или каллбэк помещаем внутрь класса ЮзерИнпут, и из него извлекаем?
    slide: Slide, user: User, callback: CallbackQuery, session: Session, state: FSMContext, db_session: AsyncSession
) -> None:
    data = await state.get_data()
    try:
        await callback.bot.edit_message_text(
            chat_id=user.telegram_id,
            message_id=data['quiz_options_msg_id'],
            text=slide.text.replace('…', f'<u>{slide.right_answers}</u>')
            if "…" in slide.text
            else slide.text + '\nSystem message!\n\nВ тексте с вопросом к квизу "выбери правильный ответ" '
            'всегда должен быть символ "…", чтобы при правильном ответе он подменялся на текст правильного варианта.',
        )
    except KeyError:
        print('something went wrong')
    await callback.message.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
    #  логгируем здесь, или на уровень выше?
    await log_quiz_answer(
        session=session,
        mode=EventType.CALLBACK_QUERY,
        event=callback,
        is_correct=True,
        slide=slide,
        db_session=db_session,
    )


async def response_wrong(
    slide: Slide, callback: CallbackQuery, state: FSMContext, session: Session, db_session: AsyncSession
) -> None:
    data = await state.get_data()
    try:
        await callback.bot.edit_message_reply_markup(
            chat_id=callback.from_user.id, message_id=data['quiz_options_msg_id']
        )
    except KeyError:
        print('something went wrong')
    await callback.message.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
    #  логгируем здесь, или на уровень выше?
    await log_quiz_answer(
        session=session,
        mode=EventType.CALLBACK_QUERY,
        event=callback,
        is_correct=False,
        slide=slide,
        db_session=db_session,
    )


async def handle_quiz(
    user: User,
    bot: Bot,
    state: FSMContext,
    user_input: UserInput,  # каллбэк отсюда, или ниже прокидываем отдельно? 4 строки ниже
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
    callback: CallbackQuery | None = None,
) -> bool:
    if not user_input:
        await show_quiz(user, bot, state, slide, session)
        return False

    match user_input:  # вот тут нужна мощная поддержка. Помочь создать класс + логику
        case UserInputHint:  # тут не всё понял, надо разобраться.
            ...
        case UserInputMsg:
            if input_correct():  # и тут не всё понял, надо разобраться.
                await response_correct(slide, user, callback, session, state, db_session)
                return True
            if error_count_exceeded(
                session.id, slide.id, db_session
            ):  # наверное надо возвращать котреж, Бул + wrong_answers_count
                await callback.message.answer(
                    text=(await get_text_by_prompt(prompt='3_wrong_answers', db_session=db_session)).format(
                        wrong_answers_count
                    ),
                    reply_markup=get_hint_keyaboard(
                        lesson_id=session.lesson_id,
                        slide_id=session.current_slide_id,
                    ),
                )
                return False
    await response_wrong(
        slide, callback, state, session, db_session
    )  # и тут не всё понял, надо разобраться. Саму проверку надо делать в match user_input, так? с этим нужна помощь
    update_error_count(session)  # в моём дизайне еррор каунт считался через каунт сешн логов, записи is_correct: False
    return False


async def handle_slide(
    user_input: UserInput,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    match slide.slide_type:
        case SlideType.TEXT:
            return await handle_text(user_input, slide, session)
        case SlideType.IMAGE:
            return await handle_image(user_input, slide, session)
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            return await handle_sticker(user_input, slide, session)
        case SlideType.PIN_DICT:
            return await handle_dict(user_input, slide, session)
        case SlideType.QUIZ_OPTIONS | SlideType.QUIZ_INPUT_PHRASE | SlideType.QUIZ_INPUT_WORD:
            return await handle_quiz(user_input, slide, session)
        case _:
            assert False, f'Unexpected slide type: {slide.slide_type}'


def finalizing(user: User, session: Session, user_input: UserInput, db_session: AsyncSession):
    if user_input:
        assert isinstance(user_input, UserInputExtraSlides)  #  нужна помощь с этим классом
        if user_input.extra_requested:
            session.set_extra()
        else:
            finish_session()  # пока не всё понятно, но до этого ещё далеко
            show_start_menu(
                user, db_session
            )  # тут надо или бота сверху передать, для отправки сообщения, или объект message
            return

    show_stats()
    if session.err_treshold is not None:  #  в сессии нет такого поля, могу завести, могу брать из лессона
        # user_errors only from exam slides quizes
        if user_errors > session.err_treshold:
            ask_for_extra()
            return
    finish_session()  # пока не всё понятно, но до этого ещё далеко
    show_start_menu(user, db_session)  # тут надо или бота сверху передать, для отправки сообщения, или объект message


async def swow_slide(
    bot: Bot,
    user: User,
    current_step: int,
    user_input: UserInput,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    while session.has_next():
        current_slide = session.get_slide()
        need_next = await handle_slide(user_input, current_step, session)
        if not need_next:
            break
        session.current_slide_id += 1  # вероятно, имеется в виду path[index(session.current_slide_id) + 1]?

    if session.in_extra:
        finalizing_extra()  # пока не всё понятно, но до этого ещё далеко
        return

    finalizing(session, user_input)  # пока не всё понятно, но до этого ещё далеко
