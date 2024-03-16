import asyncio
import logging
import os
from pathlib import Path
from random import sample

from aiogram import Bot, types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.lesson_controllers import find_first_exam_slide, session_routine
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
    update_session_status,
)
from database.models.slide import Slide
from database.models.user import User
from enums import KeyboardType, SessionStartsFrom, SessionStatus, SlideType, States, StickerType

logger = logging.Logger(__name__)


async def get_all_base_questions_id_in_lesson(
    lesson_id: int, exam_slides_id: set[int], db_session: AsyncSession
) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.lesson_id == lesson_id, Slide.slide_type.in_(all_questions_slide_types), ~Slide.id.in_(exam_slides_id)
    )
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()} if result else {}


async def get_steps_to_current_slide(first_slide_id: int, target_slide_id: int, path: str) -> int:
    slide_ids_str = path.split(".")
    slide_ids = [int(id_str) for id_str in slide_ids_str]
    start_index = slide_ids.index(first_slide_id)
    target_index = slide_ids.index(target_slide_id)
    steps = abs(target_index - start_index)
    return steps


async def set_new_slide_image(slide_id: int, image_name: str, db_session: AsyncSession):
    stmt = select(Slide).filter(Slide.id == slide_id)
    result = await db_session.execute(stmt)
    slide = result.scalar_one()
    slide.picture = image_name
    await db_session.commit()


def get_image_files_list(lesson_id: int) -> list[str]:
    directory = f'src/webapp/static/lessons_images/{lesson_id}'
    allowed_image_formats = ['png', 'jpg', 'jpeg', 'gif', 'heic', 'tiff', 'webp']
    files = []
    for filename in os.listdir(directory):
        if filename.rsplit('.', 1)[1].lower() in allowed_image_formats:
            files.append(filename)
    return files


async def slides_routine(
    slide: Slide, bot: Bot, user: User, path: list[int], current_step: int, state, session, db_session: AsyncSession
) -> None:
    next_step = current_step + 1
    try:
        next_slide_id = path[path.index(slide.id) + 1]
    except IndexError:
        next_slide_id = session.current_slide_id
    match slide.slide_type:
        case SlideType.TEXT:
            slide_text = slide.text
            if not slide.keyboard_type:
                await bot.send_message(chat_id=user.telegram_id, text=slide_text)
                if slide.delay:
                    # noinspection PyTypeChecker
                    await asyncio.sleep(slide.delay)
                await session_routine(
                    bot=bot,
                    user=user,
                    current_step=next_step,
                    slide_id=next_slide_id,
                    state=state,
                    session=session,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=session.lesson_id, next_slide=next_slide_id)
                        await bot.send_message(chat_id=user.telegram_id, text=slide_text, reply_markup=markup)
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'

        case SlideType.IMAGE:
            image_file = slide.picture
            image_path = Path(f'src/webapp/static/lessons_images/{session.lesson_id}/{image_file}')
            if not image_path.exists():
                image_path = Path(f'src/webapp/static/lessons_images/image_not_available.png')
            if not slide.keyboard_type:
                await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=image_path))
                if slide.delay:
                    # noinspection PyTypeChecker
                    await asyncio.sleep(slide.delay)
                await session_routine(
                    bot=bot,
                    user=user,
                    current_step=next_step,
                    slide_id=next_slide_id,
                    state=state,
                    session=session,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=session.lesson_id, next_slide=next_slide_id)
                        await bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=types.FSInputFile(path=image_path),
                            reply_markup=markup,
                        )
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            sticker_type = StickerType.SMALL if slide.slide_type == SlideType.SMALL_STICKER else StickerType.BIG
            await bot.send_sticker(
                chat_id=user.telegram_id,
                sticker=await get_random_sticker_id(mode=sticker_type, db_session=db_session),
            )

            await session_routine(
                bot=bot,
                user=user,
                current_step=next_step,
                slide_id=next_slide_id,
                state=state,
                session=session,
                db_session=db_session,
            )
        case SlideType.PIN_DICT:
            slide_text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=slide_text)
            await bot.pin_chat_message(
                chat_id=user.telegram_id,
                message_id=msg.message_id,
                disable_notification=True,
            )
            await session_routine(
                bot=bot,
                user=user,
                current_step=next_step,
                slide_id=next_slide_id,
                state=state,
                session=session,
                db_session=db_session,
            )
        case SlideType.QUIZ_OPTIONS:
            text = slide.text
            answer = slide.right_answers
            elements = slide.keyboard.split('|')
            options = sample(population=elements, k=len(elements))
            markup = get_quiz_keyboard(words=options, answer=answer, lesson_id=session.lesson_id, slide_id=slide.id)
            msg = await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
            await state.update_data(quiz_options_msg_id=msg.message_id)
        case SlideType.QUIZ_INPUT_WORD | SlideType.QUIZ_INPUT_PHRASE:
            slide_text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=slide_text)
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
        case _:
            assert False, f'Unexpected slide type: {slide.slide_type}'
    return


async def last_slide_processing(bot: Bot, user: User, path: list, state, session, db_session: AsyncSession) -> None:
    lesson = await get_lesson_by_id(lesson_id=session.lesson_id, db_session=db_session)
    exam_slide_id = await find_first_exam_slide(path, db_session)
    await bot.unpin_all_chat_messages(chat_id=user.telegram_id)
    await add_completed_lesson_to_db(user.id, session.lesson_id, session.id, db_session)
    await update_session_status(
        session_id=session.id,
        new_status=SessionStatus.COMPLETED,
        db_session=db_session,
    )
    all_exam_slides_in_lesson = await get_all_exam_slides_id_in_lesson(
        lesson_id=session.lesson_id, db_session=db_session
    )
    all_questions_slides_in_session = await get_all_questions_in_session(session_id=session.id, db_session=db_session)
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
            if not exam_slide_id:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=(
                        await get_text_by_prompt(prompt='final_report_without_questions', db_session=db_session)
                    ).format(lesson.title),
                    reply_markup=lesson_picker_kb,
                )
                await state.clear()
                return
            total_base_questions_in_lesson = await get_all_base_questions_id_in_lesson(
                lesson_id=session.lesson_id, exam_slides_id=all_exam_slides_in_lesson, db_session=db_session
            )
            total_base_questions_in_session = total_base_questions_in_lesson & all_questions_slides_in_session
            total_base_questions_errors = await count_errors_in_session(
                session_id=session.id, slides_set=total_base_questions_in_lesson, db_session=db_session
            )
            await bot.send_message(
                chat_id=user.telegram_id,
                text=(await get_text_by_prompt(prompt='final_report_from_begin', db_session=db_session)).format(
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
            assert False, f'Unexpected session starts from: {session_starts_from}'
    await state.clear()
