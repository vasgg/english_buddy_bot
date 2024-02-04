import asyncio
import os
from random import sample

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import Result, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.answer_controllers import get_random_sticker_id, get_text_by_prompt
from bot.controllers.session_controller import (
    count_errors_in_session,
    get_all_questions_in_session,
    get_hints_shown_counter_in_session,
    get_session,
    update_session_status,
)
from bot.controllers.session_controller import update_session
from bot.controllers.slide_controllers import get_all_base_questions_id_in_lesson, get_slide_by_id
from bot.database.models.complete_lesson import CompleteLesson
from bot.database.models.lesson import Lesson
from bot.database.models.slide import Slide
from bot.database.models.user import User
from bot.keyboards.keyboards import get_furher_button, get_lesson_picker_keyboard, get_quiz_keyboard
from bot.resources.enums import KeyboardType, SessionStartsFrom, SessionStatus, SlideType, States, StickerType


async def get_lesson(lesson_id: int, db_session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.id == lesson_id)
    result: Result = await db_session.execute(query)
    return result.scalar()


async def get_lessons(db_session: AsyncSession) -> list[Lesson]:
    query = select(Lesson)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    return [row for row in lessons]


async def add_completed_lesson_to_db(user_id: int, lesson_id: int, session_id: int, db_session: AsyncSession) -> None:
    completed_lesson = CompleteLesson(
        user_id=user_id,
        lesson_id=lesson_id,
        session_id=session_id,
    )
    db_session.add(completed_lesson)


async def get_completed_lessons(user_id: int, db_session: AsyncSession) -> set[int]:
    query = select(CompleteLesson.lesson_id).filter(CompleteLesson.user_id == user_id)
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()}


async def get_all_exam_slides_id_in_lesson(lesson_id: int, db_session: AsyncSession) -> set[int]:
    query = select(Slide.id).filter(Slide.lesson_id == lesson_id, Slide.is_exam_slide)
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()} if result else {}


async def lesson_routine(
    bot: Bot,
    user: User,
    lesson_id: int,
    slide_id: int,
    current_step: int,
    total_slides: int,
    state: FSMContext,
    session_id: int,
    db_session: AsyncSession,
) -> None:
    progress = f'<i>{current_step}/{total_slides}</i>\n\n'
    slide: Slide = await get_slide_by_id(slide_id=slide_id, db_session=db_session)
    await update_session(
        user_id=user.id,
        lesson_id=lesson_id,
        current_slide_id=slide.id,
        current_step=current_step,
        session_id=session_id,
        db_session=db_session,
    )
    match slide.slide_type:
        case SlideType.TEXT:
            text = progress + slide.text
            if not slide.keyboard_type:
                await bot.send_message(chat_id=user.telegram_id, text=text)
                if slide.delay:
                    # noinspection PyTypeChecker
                    await asyncio.sleep(slide.delay)
                await lesson_routine(
                    bot=bot,
                    user=user,
                    lesson_id=lesson_id,
                    slide_id=slide.next_slide,
                    current_step=current_step + 1,
                    total_slides=total_slides,
                    state=state,
                    session_id=session_id,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_id, next_slide=slide.next_slide)
                        await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'

        case SlideType.IMAGE:
            image_file = slide.picture
            print(os.getcwd())
            path = f'src/webapp/static/images/lesson{lesson_id}/{image_file}'
            if not slide.keyboard_type:
                await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=path))
                if slide.delay:
                    # noinspection PyTypeChecker
                    await asyncio.sleep(slide.delay)
                await lesson_routine(
                    bot=bot,
                    user=user,
                    lesson_id=lesson_id,
                    slide_id=slide.next_slide,
                    current_step=current_step + 1,
                    total_slides=total_slides,
                    state=state,
                    session_id=session_id,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_id, next_slide=slide.next_slide)
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
                slide_id=slide.next_slide,
                current_step=current_step + 1,
                total_slides=total_slides,
                state=state,
                session_id=session_id,
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
                slide_id=slide.next_slide,
                current_step=current_step + 1,
                total_slides=total_slides,
                state=state,
                session_id=session_id,
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
                slide_id=slide.next_slide,
                current_step=current_step + 1,
                total_slides=total_slides,
                state=state,
                session_id=session_id,
                db_session=db_session,
            )
        case SlideType.QUIZ_OPTIONS:
            text = progress + slide.text
            answer = slide.right_answers
            options = sample(population=slide.keyboard.split('|'), k=3)
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
            text = progress + slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            await state.update_data(
                quiz_phrase_msg_id=msg.message_id,
                quiz_phrase_lesson_id=lesson_id,
                quiz_phrase_slide_id=slide_id,
            )
            await state.set_state(States.INPUT_PHRASE)
        case SlideType.FINAL_SLIDE:
            text = progress + slide.text
            lesson = await get_lesson(lesson_id=lesson_id, db_session=db_session)
            session = await get_session(session_id=session_id, db_session=db_session)
            await bot.send_message(chat_id=user.telegram_id, text=text)
            await bot.unpin_all_chat_messages(chat_id=user.telegram_id)
            await add_completed_lesson_to_db(user.id, lesson_id, session_id, db_session)
            await update_session_status(
                session_id=session_id,
                new_status=SessionStatus.COMPLETED,
                db_session=db_session,
            )
            all_exam_slides_in_lesson = await get_all_exam_slides_id_in_lesson(
                lesson_id=lesson_id, db_session=db_session
            )
            all_questions_slides_in_session = await get_all_questions_in_session(
                session_id=session_id, db_session=db_session
            )
            total_exam_questions_in_session = all_exam_slides_in_lesson & all_questions_slides_in_session
            total_exam_questions_errors = await count_errors_in_session(
                session_id=session_id, slides_set=total_exam_questions_in_session, db_session=db_session
            )
            hints_shown = await get_hints_shown_counter_in_session(session_id=session_id, db_session=db_session)
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
                        session_id=session_id, slides_set=total_base_questions_in_lesson, db_session=db_session
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


async def update_lesson_first_slide(lesson_id: int, first_slide_id: int, db_session):
    await db_session.execute(update(Lesson).where(Lesson.id == lesson_id).values(first_slide_id=first_slide_id))


async def update_lesson_exam_slide(lesson_id: int, exam_slide_id: int, db_session):
    await db_session.execute(update(Lesson).where(Lesson.id == lesson_id).values(exam_slide_id=exam_slide_id))
