import asyncio
import logging
from pathlib import Path
from random import sample

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.slide_controllers import get_all_base_questions_id_in_lesson
from bot.keyboards.keyboards import get_furher_button, get_lesson_picker_keyboard, get_quiz_keyboard
from database.crud.answer import get_random_sticker_id, get_text_by_prompt
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
    get_hints_shown_counter_in_session,
    update_session,
    update_session_status,
)
from database.crud.slide import get_slide_by_id
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User
from enums import KeyboardType, SessionStartsFrom, SessionStatus, SlideType, States, StickerType

logger = logging.Logger(__name__)


async def lesson_routine(
    bot: Bot,
    user: User,
    lesson_id: int,
    slide_id: int,
    current_step: int,
    total_slides: int,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    # progress = f'<i>{current_step}/{total_slides}</i>\n\n'
    slide: Slide = await get_slide_by_id(slide_id=slide_id, db_session=db_session)
    slide_ids = [int(elem) for elem in session.path.split(".")]
    if not slide:
        logger.error(f'Slide {slide_id} not found')
        return
    if not slide.text:
        slide.text = 'System message. Please add slide text in admin panel.'
    await update_session(
        user_id=user.id,
        lesson_id=lesson_id,
        current_slide_id=slide.id,
        current_step=current_step,
        session_id=session.id,
        db_session=db_session,
    )
    match slide.slide_type:
        case SlideType.TEXT:
            text = slide.text
            if not slide.keyboard_type:
                await bot.send_message(chat_id=user.telegram_id, text=text)
                if slide.delay:
                    # noinspection PyTypeChecker
                    await asyncio.sleep(slide.delay)
                await lesson_routine(
                    bot=bot,
                    user=user,
                    lesson_id=lesson_id,
                    slide_id=slide_ids[slide_ids.index(slide.id) + 1],
                    current_step=current_step + 1,
                    total_slides=total_slides,
                    state=state,
                    session=session,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(
                            current_lesson=lesson_id, next_slide=slide_ids[slide_ids.index(slide.id) + 1]
                        )
                        await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'

        case SlideType.IMAGE:
            image_file = slide.picture
            path = Path(f'src/webapp/static/lessons_images/{lesson_id}/{image_file}')
            if not path.exists():
                path = Path(f'src/webapp/static/images/lessons_images/image_not_available.png')
            if not slide.keyboard_type:
                await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=path))
                if slide.delay:
                    # noinspection PyTypeChecker
                    await asyncio.sleep(slide.delay)
                await lesson_routine(
                    bot=bot,
                    user=user,
                    lesson_id=lesson_id,
                    slide_id=slide_ids[slide_ids.index(slide.id) + 1],
                    current_step=current_step + 1,
                    total_slides=total_slides,
                    state=state,
                    session=session,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(
                            current_lesson=lesson_id, next_slide=slide_ids[slide_ids.index(slide.id) + 1]
                        )
                        await bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=types.FSInputFile(path=path),
                            reply_markup=markup,
                        )
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'
        case SlideType.SMALL_STICKER:
            await bot.send_sticker(
                chat_id=user.telegram_id,
                sticker=await get_random_sticker_id(mode=StickerType.SMALL, db_session=db_session),
            )
            await lesson_routine(
                bot=bot,
                user=user,
                lesson_id=lesson_id,
                slide_id=slide_ids[slide_ids.index(slide.id) + 1],
                current_step=current_step + 1,
                total_slides=total_slides,
                state=state,
                session=session,
                db_session=db_session,
            )
        case SlideType.BIG_STICKER:
            await bot.send_sticker(
                chat_id=user.telegram_id,
                sticker=await get_random_sticker_id(mode=StickerType.BIG, db_session=db_session),
            )
            await lesson_routine(
                bot=bot,
                user=user,
                lesson_id=lesson_id,
                slide_id=slide_ids[slide_ids.index(slide.id) + 1],
                current_step=current_step + 1,
                total_slides=total_slides,
                state=state,
                session=session,
                db_session=db_session,
            )
        case SlideType.PIN_DICT:
            text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            await bot.pin_chat_message(
                chat_id=user.telegram_id,
                message_id=msg.message_id,
                disable_notification=True,
            )
            await lesson_routine(
                bot=bot,
                user=user,
                lesson_id=lesson_id,
                slide_id=slide_ids[slide_ids.index(slide.id) + 1],
                current_step=current_step + 1,
                total_slides=total_slides,
                state=state,
                session=session,
                db_session=db_session,
            )
        case SlideType.QUIZ_OPTIONS:
            text = slide.text
            answer = slide.right_answers
            elements = slide.keyboard.split('|')
            options = sample(population=elements, k=len(elements))
            markup = get_quiz_keyboard(words=options, answer=answer, lesson_id=lesson_id, slide_id=slide.id)
            msg = await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
            await state.update_data(quiz_options_msg_id=msg.message_id)
        case SlideType.QUIZ_INPUT_WORD:
            text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            await state.update_data(
                quiz_word_msg_id=msg.message_id,
                quiz_word_lesson_id=lesson_id,
                quiz_word_slide_id=slide_id,
            )
            await state.set_state(States.INPUT_WORD)
        case SlideType.QUIZ_INPUT_PHRASE:
            text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            await state.update_data(
                quiz_phrase_msg_id=msg.message_id,
                quiz_phrase_lesson_id=lesson_id,
                quiz_phrase_slide_id=slide_id,
            )
            await state.set_state(States.INPUT_PHRASE)
        case SlideType.FINAL_SLIDE:
            text = slide.text
            lesson = await get_lesson_by_id(lesson_id=lesson_id, db_session=db_session)
            await bot.send_message(chat_id=user.telegram_id, text=text)
            await bot.unpin_all_chat_messages(chat_id=user.telegram_id)
            await add_completed_lesson_to_db(user.id, lesson_id, session.id, db_session)
            await update_session_status(
                session_id=session.id,
                new_status=SessionStatus.COMPLETED,
                db_session=db_session,
            )
            all_exam_slides_in_lesson = await get_all_exam_slides_id_in_lesson(
                lesson_id=lesson_id, db_session=db_session
            )
            all_questions_slides_in_session = await get_all_questions_in_session(
                session_id=session.id, db_session=db_session
            )
            total_exam_questions_in_session = all_exam_slides_in_lesson & all_questions_slides_in_session
            total_exam_questions_errors = await count_errors_in_session(
                session_id=session.id, slides_set=total_exam_questions_in_session, db_session=db_session
            )
            hints_shown = await get_hints_shown_counter_in_session(session_id=session.id, db_session=db_session)
            session_starts_from = session.starts_from
            lessons = await get_lessons(db_session)
            completed_lessons = await get_completed_lessons(user_id=user.id, db_session=db_session)
            lesson_picker_kb = get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons)
            match session_starts_from:
                case SessionStartsFrom.BEGIN:
                    if not lesson.exam_slide_id:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=(
                                await get_text_by_prompt(
                                    prompt='final_report_without_questions', db_session=db_session
                                )
                            ).format(lesson.title),
                            reply_markup=lesson_picker_kb,
                        )
                        await state.clear()
                        return
                    total_base_questions_in_lesson = await get_all_base_questions_id_in_lesson(
                        lesson_id=lesson_id, exam_slides_id=all_exam_slides_in_lesson, db_session=db_session
                    )
                    total_base_questions_in_session = total_base_questions_in_lesson & all_questions_slides_in_session
                    total_base_questions_errors = await count_errors_in_session(
                        session_id=session.id, slides_set=total_base_questions_in_lesson, db_session=db_session
                    )
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=(
                            await get_text_by_prompt(prompt='final_report_from_begin', db_session=db_session)
                        ).format(
                            lesson.title,
                            len(total_base_questions_in_session) - total_base_questions_errors,
                            len(total_base_questions_in_session),
                            len(total_exam_questions_in_session) - total_exam_questions_errors,
                            len(total_exam_questions_in_session),
                            hints_shown,
                        ),
                        reply_markup=lesson_picker_kb,
                    )
                case SessionStartsFrom.EXAM:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=(await get_text_by_prompt(prompt='final_report_from_exam', db_session=db_session)).format(
                            lesson.title,
                            len(total_exam_questions_in_session) - total_exam_questions_errors,
                            len(total_exam_questions_in_session),
                            hints_shown,
                        ),
                        reply_markup=lesson_picker_kb,
                    )
                case _:
                    assert False, f'Unknown session starts from: {session_starts_from}'
            await state.clear()
            return
        case _:
            assert False, f'Unknown slide type: {slide.slide_type}'
