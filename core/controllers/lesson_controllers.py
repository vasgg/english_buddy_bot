import asyncio
from random import sample

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import Result, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.choice_controllers import get_random_sticker_id
from core.controllers.session_controller import (
    count_distinct_slides_by_type,
    count_errors_in_slides_by_type,
    get_session,
    update_session_status,
)
from core.controllers.slide_controllers import get_slide_by_id
from core.controllers.user_controllers import update_session
from core.database.models import Lesson, Slide, User, UserCompleteLesson
from core.keyboards.keyboards import get_furher_button, get_quiz_keyboard
from core.resources.answers import replies
from core.resources.enums import (
    CountQuizSlidesMode,
    KeyboardType,
    SessionStatus,
    SessionStartsFrom,
    SlideType,
    States,
)
from core.resources.stickers import big_stickers, small_stickers


async def get_lesson(lesson_id: int, db_session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.id == lesson_id)
    result: Result = await db_session.execute(query)
    lesson = result.scalar()
    return lesson


async def get_lessons(db_session: AsyncSession) -> list[Lesson]:
    query = select(Lesson)
    result = await db_session.execute(query)
    lessons = result.scalars().all()
    return [row for row in lessons]


async def add_completed_lesson_to_db(
    user_id: int, lesson_id: int, db_session: AsyncSession
) -> None:
    upsert_query = insert(UserCompleteLesson).values(
        user_id=user_id, lesson_id=lesson_id
    )
    upsert_query = upsert_query.on_conflict_do_nothing()
    await db_session.execute(upsert_query)


async def get_completed_lessons(user_id: int, db_session: AsyncSession) -> set[int]:
    query = select(UserCompleteLesson.lesson_id).filter(
        UserCompleteLesson.user_id == user_id
    )
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()}


async def lesson_routine(
    bot: Bot,
    user: User,
    lesson_id: int,
    slide_id: int,
    state: FSMContext,
    session_id: int,
    db_session: AsyncSession,
) -> None:
    slide: Slide = await get_slide_by_id(
        lesson_id=lesson_id, slide_id=slide_id, db_session=db_session
    )
    await update_session(
        user_id=user.id,
        lesson_id=lesson_id,
        current_slide_id=slide.id,
        session_id=session_id,
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
                    slide_id=slide.next_slide,
                    state=state,
                    session_id=session_id,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(
                            current_lesson=lesson_id, next_slide=slide.next_slide
                        )
                        await bot.send_message(
                            chat_id=user.telegram_id, text=text, reply_markup=markup
                        )
                    case _:
                        assert False, f"Unknown keyboard type: {slide.keyboard_type}"

        case SlideType.IMAGE:
            image_file = slide.picture
            path = f"core/resources/images/lesson{lesson_id}/{image_file}"
            if not slide.keyboard_type:
                await bot.send_photo(
                    chat_id=user.telegram_id, photo=types.FSInputFile(path=path)
                )
                if slide.delay:
                    # noinspection PyTypeChecker
                    await asyncio.sleep(slide.delay)
                await lesson_routine(
                    bot=bot,
                    user=user,
                    lesson_id=lesson_id,
                    slide_id=slide.next_slide,
                    state=state,
                    session_id=session_id,
                    db_session=db_session,
                )
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(
                            current_lesson=lesson_id, next_slide=slide.next_slide
                        )
                        await bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=types.FSInputFile(path=path),
                            reply_markup=markup,
                        )
                    case _:
                        assert False, f"Unknown keyboard type: {slide.keyboard_type}"
        case SlideType.SMALL_STICKER:
            await bot.send_sticker(
                chat_id=user.telegram_id,
                sticker=get_random_sticker_id(collection=small_stickers),
            )
            await lesson_routine(
                bot=bot,
                user=user,
                lesson_id=lesson_id,
                slide_id=slide.next_slide,
                state=state,
                session_id=session_id,
                db_session=db_session,
            )
        case SlideType.BIG_STICKER:
            await bot.send_sticker(
                chat_id=user.telegram_id,
                sticker=get_random_sticker_id(collection=big_stickers),
            )
            await lesson_routine(
                bot=bot,
                user=user,
                lesson_id=lesson_id,
                slide_id=slide.next_slide,
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
                state=state,
                session_id=session_id,
                db_session=db_session,
            )
        case SlideType.QUIZ_OPTIONS:
            text = slide.text
            answer = slide.right_answers
            options = sample(population=slide.keyboard.split("|"), k=3)
            markup = get_quiz_keyboard(
                words=options, answer=answer, lesson_id=lesson_id, slide_id=slide.id
            )
            msg = await bot.send_message(
                chat_id=user.telegram_id, text=text, reply_markup=markup
            )
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
            await bot.send_message(chat_id=user.telegram_id, text=text)
            lesson = await get_lesson(lesson_id=lesson_id, db_session=db_session)
            exam_slides_type = lesson.exam_slide_type
            session = await get_session(session_id=session_id, db_session=db_session)
            total_exam_questions = await count_distinct_slides_by_type(
                session_id=session_id,
                mode=CountQuizSlidesMode.WITH_TYPE,
                slide_type=exam_slides_type,
                db_session=db_session,
            )
            total_exam_questions_errors = await count_errors_in_slides_by_type(
                session_id=session_id,
                mode=CountQuizSlidesMode.WITH_TYPE,
                slide_type=exam_slides_type,
                db_session=db_session,
            )
            session_starts_from = session.starts_from
            match session_starts_from:
                case SessionStartsFrom.BEGIN:
                    total_base_questions = await count_distinct_slides_by_type(
                        session_id=session_id,
                        mode=CountQuizSlidesMode.WITHOUT_TYPE,
                        slide_type=exam_slides_type,
                        db_session=db_session,
                    )
                    total_base_questions_errors = await count_errors_in_slides_by_type(
                        session_id=session_id,
                        mode=CountQuizSlidesMode.WITHOUT_TYPE,
                        slide_type=exam_slides_type,
                        db_session=db_session,
                    )
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=replies["final_report_from_begin"].format(
                            lesson.title,
                            total_base_questions - total_base_questions_errors,
                            total_base_questions,
                            total_exam_questions - total_exam_questions_errors,
                            total_exam_questions,
                        ),
                    )
                case SessionStartsFrom.EXAM:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=replies["final_report_from_exam"].format(
                            lesson.title,
                            total_exam_questions - total_exam_questions_errors,
                            total_exam_questions,
                        ),
                    )
                case _:
                    assert False, f"Unknown session starts from: {session_starts_from}"
            await bot.unpin_all_chat_messages(chat_id=user.telegram_id)
            await add_completed_lesson_to_db(user.id, lesson_id, db_session)
            await update_session_status(
                session_id=session_id,
                new_status=SessionStatus.COMPLETED,
                db_session=db_session,
            )
            await state.clear()
            return
        case _:
            assert False, f"Unknown slide type: {slide.slide_type}"
