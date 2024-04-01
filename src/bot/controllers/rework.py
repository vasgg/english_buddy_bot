import asyncio
import logging
from pathlib import Path
from random import sample

from aiogram import types
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.lesson_controllers import find_first_exam_slide_id
from bot.controllers.session_controller import log_quiz_answer
from bot.controllers.slide_controllers import get_all_base_questions_id_in_lesson
from bot.controllers.user_controllers import show_start_menu
from bot.keyboards.callback_data import ExtraSlidesCallbackFactory, HintCallbackFactory, UserInputCallbackFactory
from bot.keyboards.keyboards import (
    get_extra_slides_keyaboard,
    get_hint_keyaboard,
    get_lesson_picker_keyboard,
    get_new_furher_button,
    get_quiz_keyboard,
)
from database.crud.answer import get_random_answer, get_random_sticker_id, get_text_by_prompt
from database.crud.lesson import (
    add_completed_lesson_to_db,
    get_all_exam_slides_id_in_lesson,
    get_completed_lessons,
    get_lesson_by_id,
    get_lessons,
)
from database.crud.session import (
    count_errors_in_session,
    get_all_questions_in_session,
    get_wrong_answers_counter,
    update_session_status,
)
from database.crud.user import get_user_from_db
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from enums import KeyboardType, ReactionType, SessionStartsFrom, SessionStatus, SlideType, States, StickerType


class UserStats(BaseModel):
    regular_exercises: int | None
    exam_exercises: int | None
    correct_regular_answers: int | None
    correct_exam_answers: int | None


class UserInputMsg(BaseModel):
    text: str


class UserInputHint(BaseModel):
    hint_requested: bool


class UserInputExtraSlides(BaseModel):
    extra_requested: bool


UserQuizInput = UserInputMsg | UserInputHint | None


UserAnswerInput = UserInputCallbackFactory | HintCallbackFactory | ExtraSlidesCallbackFactory


async def handle_text(
    event: types.Message,
    slide: Slide,
) -> bool:
    markup = None
    if slide.keyboard_type == KeyboardType.FURTHER:
        markup = get_new_furher_button()
    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    await event.answer(
        text=slide.text,
        reply_markup=markup,
    )
    return slide.keyboard_type != KeyboardType.FURTHER


async def handle_image(
    event: types.Message,
    slide: Slide,
    session: Session,
) -> bool:
    markup = None
    image_path = Path(f'src/webapp/static/lessons_images/{session.lesson_id}/{slide.picture}')
    if not image_path.exists():
        image_path = Path(f'src/webapp/static/lessons_images/Image_not_available.png')
    if slide.keyboard_type == KeyboardType.FURTHER:
        markup = get_new_furher_button()
    await event.answer_photo(photo=types.FSInputFile(path=image_path), reply_markup=markup)
    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    return slide.keyboard_type != KeyboardType.FURTHER


async def handle_sticker(
    event: types.Message,
    slide_type: SlideType,
    db_session: AsyncSession,
) -> bool:
    sticker_type = StickerType.SMALL if slide_type == SlideType.SMALL_STICKER else StickerType.BIG
    await event.answer_sticker(sticker=await get_random_sticker_id(mode=sticker_type, db_session=db_session))
    return True


async def handle_dict(
    event: types.Message,
    text: str,
) -> bool:
    msg = await event.answer(text=text)
    await event.bot.pin_chat_message(
        chat_id=event.from_user.id,
        message_id=msg.message_id,
        disable_notification=True,
    )
    return True


async def show_quiz_options(
    event: types.Message,
    lesson_id: int,
    state: FSMContext,
    slide: Slide,
) -> bool:
    right_answer = slide.right_answers
    wrong_answers = slide.keyboard.split('|')
    elements = [right_answer, *wrong_answers]
    options = sample(population=elements, k=len(elements))
    markup = get_quiz_keyboard(words=options, answer=right_answer, lesson_id=lesson_id, slide_id=slide.id)
    msg = await event.answer(text=slide.text, reply_markup=markup)
    await state.update_data(quiz_options_msg_id=msg.message_id)
    return False


async def show_quiz_input_word(
    event: types.Message,
    state: FSMContext,
    slide: Slide,
) -> bool:
    msg = await event.answer(text=slide.text)
    await state.update_data(quiz_word_msg_id=msg.message_id)
    await state.set_state(States.INPUT_WORD)
    return False


async def show_quiz_input_phrase(
    event: types.Message,
    state: FSMContext,
    slide: Slide,
) -> bool:
    msg = await event.answer(text=slide.text)
    await state.update_data(quiz_phrase_msg_id=msg.message_id)
    await state.set_state(States.INPUT_PHRASE)
    return False


async def error_count_exceeded(session_id: int, slide_id: int, db_session: AsyncSession) -> bool:
    wrong_answers_count = await get_wrong_answers_counter(session_id, slide_id, db_session)
    if wrong_answers_count >= 3:
        return True
    return False


async def response_options_correct(
    event: types.Message,
    slide: Slide,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    data = await state.get_data()
    try:
        await event.bot.edit_message_text(
            chat_id=event.from_user.id,
            message_id=data['quiz_options_msg_id'],
            text=slide.text.replace('…', f'<u>{slide.right_answers}</u>')
            if "…" in slide.text
            else slide.text + '\nSystem message!\n\nВ тексте с вопросом к квизу "выбери правильный ответ" '
            'всегда должен быть символ "…", чтобы при правильном ответе он подменялся на текст правильного варианта.',
        )
    except KeyError:
        logging.exception('something went wrong with quiz_options')
    await event.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
    await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)


async def response_options_wrong(
    event: types.Message,
    slide: Slide,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    data = await state.get_data()
    try:
        await event.bot.edit_message_reply_markup(chat_id=event.from_user.id, message_id=data['quiz_options_msg_id'])
    except KeyError:
        logging.exception('something went wrong with quiz_options')
    await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
    await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
    await show_quiz_options(event, session.lesson_id, state, slide)


async def response_input_word_correct(
    event: types.Message,
    slide: Slide,
    user_input: UserAnswerInput,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    data = await state.get_data()
    try:
        await event.bot.edit_message_text(
            chat_id=event.from_user.id,
            message_id=data["quiz_word_msg_id"],
            text=slide.text.replace("…", f"<u>{user_input.text.lower()}</u>")
            if "…" in slide.text
            else slide.text + '\nSystem message!\n\nВ тексте с вопросом к квизу "впиши слово" '
            'всегда должен быть символ "…", чтобы при правильном ответе он подменялся на текст правильного варианта.',
        )
    except KeyError:
        logging.exception('something went wrong with quiz_input_word')
    await event.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
    await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)


async def response_input_word_almost_correct(
    event: types.Message,
    slide: Slide,
    user_input: UserAnswerInput,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    data = await state.get_data()
    try:
        await event.bot.edit_message_text(
            chat_id=event.from_user.id,
            message_id=data["quiz_word_msg_id"],
            text=slide.text.replace("…", f"<u>{user_input.text.lower()}</u>")
            if "…" in slide.text
            else slide.text + '\nSystem message!\n\nВ тексте с вопросом к квизу "впиши слово" '
            'всегда должен быть символ "…", чтобы при правильном ответе он подменялся на текст правильного варианта.',
        )
    except KeyError:
        logging.exception('something went wrong with quiz_input_word')
    await event.answer(text=slide.almost_right_answer_reply)
    await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)


async def response_input_phrase_correct(
    event: types.Message,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> None:
    await event.answer(text=await get_random_answer(mode=ReactionType.RIGHT, db_session=db_session))
    await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)


async def response_input_phrase_almost_correct(
    event: types.Message,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> None:
    await event.answer(text=slide.almost_right_answer_reply)
    await log_quiz_answer(session.id, slide.id, slide.slide_type, True, db_session)


async def response_input_wrong(
    event: types.Message,
    slide: Slide,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
    await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
    if slide.slide_type == SlideType.QUIZ_INPUT_WORD:
        await show_quiz_input_word(event, state, slide)
    else:
        await show_quiz_input_phrase(event, state, slide)


async def show_hint_dialog(
    event: types.Message,
    db_session: AsyncSession,
):
    await event.answer(
        text=(await get_text_by_prompt(prompt='3_wrong_answers', db_session=db_session)),
        reply_markup=get_hint_keyaboard(),
    )


async def handle_quiz_options(
    event: types.Message,
    state: FSMContext,
    user_input: UserAnswerInput,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    if not user_input:
        return await show_quiz_options(event, session.lesson_id, state, slide)
    match user_input:
        case UserInputHint() as hint_msg:
            if hint_msg.hint_requested:
                await event.answer(
                    text=(await get_text_by_prompt(prompt='right_answer', db_session=db_session)).format(
                        slide.right_answers
                    ),
                )
                await asyncio.sleep(2)
                return True
            else:
                await event.edit_reply_markup()
                return await show_quiz_options(event, session.lesson_id, state, slide)
        case UserInputMsg() as input_msg:
            if input_msg.text.lower() == slide.right_answers.lower():
                await response_options_correct(event, slide, state, session, db_session)
                return True
            if error_count_exceeded(session.id, slide.id, db_session):
                await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
                await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
                await show_hint_dialog(event, db_session)
                return False
            await response_options_wrong(event, slide, state, session, db_session)
            return False


async def handle_quiz_input_word(
    event: types.Message,
    state: FSMContext,
    user_input: UserAnswerInput,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    if not user_input:
        return await show_quiz_input_word(event, state, slide)
    match user_input:
        case UserInputHint() as hint_msg:
            if hint_msg.hint_requested:
                await event.answer(
                    text=(await get_text_by_prompt(prompt='right_answer', db_session=db_session)).format(
                        slide.right_answers if '|' not in slide.right_answers else slide.right_answers.split('|')[0]
                    ),
                )
                await asyncio.sleep(2)
                return True
            else:
                return await show_quiz_input_word(event, state, slide)
        case UserInputMsg() as input_msg:
            answers_lower = [answer.lower() for answer in slide.right_answers.split("|")]
            almost_right_answers_lower = [answer.lower() for answer in slide.almost_right_answers.split("|")]
            if input_msg.text.lower() in answers_lower:
                await response_input_word_correct(event, slide, user_input, state, session, db_session)
                return True
            elif input_msg.text.lower() in almost_right_answers_lower:
                await response_input_word_almost_correct(event, slide, user_input, state, session, db_session)
                return True
            if error_count_exceeded(session.id, slide.id, db_session):
                await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
                await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
                await show_hint_dialog(event, db_session)
                return False
            await response_input_wrong(event, slide, state, session, db_session)
            return False


async def handle_quiz_input_phrase(
    event: types.Message,
    state: FSMContext,
    user_input: UserAnswerInput,
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
                        slide.right_answers if '|' not in slide.right_answers else slide.right_answers.split('|')[0]
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
                await response_input_phrase_correct(event, slide, session, db_session)
                return True
            elif input_msg.text.lower() in almost_right_answers_lower:
                await response_input_phrase_almost_correct(event, slide, session, db_session)
                return True
            if error_count_exceeded(session.id, slide.id, db_session):
                await event.answer(text=await get_random_answer(mode=ReactionType.WRONG, db_session=db_session))
                await log_quiz_answer(session.id, slide.id, slide.slide_type, False, db_session)
                await show_hint_dialog(event, db_session)
                return False
            await response_input_wrong(event, slide, state, session, db_session)
            return False


async def handle_slide(
    event: types.Message,
    state: FSMContext,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
    user_input: UserAnswerInput | None = None,
) -> bool:
    match slide.slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            return await handle_sticker(event, slide.slide_type, db_session)
        case SlideType.TEXT:
            return await handle_text(event, slide)
        case SlideType.IMAGE:
            return await handle_image(event, slide, session)
        case SlideType.PIN_DICT:
            return await handle_dict(event, slide.text)
        case SlideType.QUIZ_OPTIONS:
            return await handle_quiz_options(event, state, user_input, slide, session, db_session)
        case SlideType.QUIZ_INPUT_WORD:
            return await handle_quiz_input_word(event, state, user_input, slide, session, db_session)
        case SlideType.QUIZ_INPUT_PHRASE:
            return await handle_quiz_input_phrase(event, state, user_input, slide, session, db_session)
        case _:
            assert False, f'Unexpected slide type: {slide.slide_type}'


async def finish_session(user_id: int, session: Session, db_session: AsyncSession) -> None:
    await add_completed_lesson_to_db(user_id, session.lesson_id, session.id, db_session)
    await update_session_status(
        session_id=session.id,
        new_status=SessionStatus.COMPLETED,
        db_session=db_session,
    )


async def show_stats(
    event: types.Message, stats: UserStats, state: FSMContext, session: Session, db_session: AsyncSession
) -> None:
    lesson = await get_lesson_by_id(lesson_id=session.lesson_id, db_session=db_session)
    lessons = await get_lessons(db_session)
    exam_slide_id = await find_first_exam_slide_id(session.get_path(), db_session)
    completed_lessons = await get_completed_lessons(user_id=event.from_user.id, db_session=db_session)
    lesson_picker_kb = get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons)
    match session.starts_from:
        case SessionStartsFrom.BEGIN:
            if not exam_slide_id:
                await event.answer(
                    text=(
                        await get_text_by_prompt(prompt='final_report_without_questions', db_session=db_session)
                    ).format(lesson.title),
                    reply_markup=lesson_picker_kb,
                )
                await state.clear()
                return
            await event.answer(
                text=(await get_text_by_prompt(prompt='final_report_from_begin', db_session=db_session)).format(
                    lesson.title,
                    stats.correct_regular_answers,
                    stats.regular_exercises,
                    stats.correct_exam_answers,
                    stats.exam_exercises,
                ),
                reply_markup=lesson_picker_kb,
            )
        case SessionStartsFrom.EXAM:
            await event.answer(
                text=(await get_text_by_prompt(prompt='final_report_from_exam', db_session=db_session)).format(
                    lesson.title,
                    stats.correct_exam_answers,
                    stats.exam_exercises,
                ),
                reply_markup=lesson_picker_kb,
            )
        case _:
            assert False, f'Unexpected session starts from: {session.starts_from}'


async def show_extra_slides_dialog(
    event: types.Message,
    db_session: AsyncSession,
) -> None:
    await event.answer(
        text=(await get_text_by_prompt(prompt='extra_slides_dialog', db_session=db_session)),
        reply_markup=get_extra_slides_keyaboard(),
    )


async def calculate_user_stats(session: Session, db_session: AsyncSession) -> UserStats:
    all_exam_slides_in_lesson = await get_all_exam_slides_id_in_lesson(
        lesson_id=session.lesson_id, db_session=db_session
    )
    all_questions_slides_in_session = await get_all_questions_in_session(session_id=session.id, db_session=db_session)
    total_exam_questions_in_session = all_exam_slides_in_lesson & all_questions_slides_in_session
    total_exam_questions_errors = await count_errors_in_session(
        session_id=session.id, slides_set=total_exam_questions_in_session, db_session=db_session
    )
    total_base_questions_in_lesson = await get_all_base_questions_id_in_lesson(
        lesson_id=session.lesson_id, exam_slides_id=all_exam_slides_in_lesson, db_session=db_session
    )
    total_base_questions_in_session = total_base_questions_in_lesson & all_questions_slides_in_session
    total_base_questions_errors = await count_errors_in_session(
        session_id=session.id, slides_set=total_base_questions_in_lesson, db_session=db_session
    )
    stats = UserStats(
        regular_exercises=len(total_base_questions_in_session),
        exam_exercises=len(total_exam_questions_in_session),
        correct_regular_answers=len(total_base_questions_in_session) - total_base_questions_errors,
        correct_exam_answers=len(total_exam_questions_in_session) - total_exam_questions_errors,
    )
    return stats


async def finalizing_extra() -> None:
    pass


async def handle_extra_slide_answer(
    event: types.Message,
    user_input: UserInputExtraSlides,
    session: Session,
    db_session: AsyncSession,
) -> None:
    if user_input.extra_requested:
        session.set_extra()
    else:
        await finish_session(event.from_user.id, session, db_session)
        await show_start_menu(event, db_session)
        return


async def handle_user_input(
    event: types.Message, state: FSMContext, session: Session, db_session: AsyncSession
) -> None:
    await show_slide(event, state, session, db_session)


async def finalizing(event: types.Message, state: FSMContext, session: Session, db_session: AsyncSession):
    await event.bot.unpin_all_chat_messages(chat_id=event.from_user.id)
    user_stats: UserStats = await calculate_user_stats(session, db_session)
    await show_stats(event, user_stats, state, session, db_session)
    lesson: Lesson = await get_lesson_by_id(session.lesson_id, db_session)
    if lesson.errors_threshold is not None:
        percentage = (user_stats.correct_exam_answers / user_stats.exam_exercises) * 100
        if percentage < lesson.errors_threshold:
            await show_extra_slides_dialog(event, db_session)
            return
    user = await get_user_from_db(event.from_user.id, db_session)
    await finish_session(user.id, session, db_session)
    await show_start_menu(event, db_session)
    await state.clear()


async def show_slide(
    event: types.Message,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
    user_input: UserAnswerInput | None = None,
) -> None:
    while session.has_next():
        current_slide = session.get_slide()
        need_next = await handle_slide(event, state, current_slide, session, db_session, user_input)
        if not need_next:
            break

        session.current_step += 1
        await db_session.flush()

    if session.in_extra:
        await finalizing_extra()
        return

    await finalizing(event, state, session, db_session)
