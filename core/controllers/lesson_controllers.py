import asyncio
from random import sample

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import Result, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.slide_controllers import get_slide_by_id
from core.controllers.choice_controllers import get_random_sticker_id
from core.controllers.user_controllers import mark_lesson_as_completed, update_session
from core.database.models import Lesson, User, UserCompleteLesson
from core.keyboards.keyboards import get_furher_button, get_quiz_keyboard
from core.resources.enums import KeyboardType, SlideType, StartsFrom, States
from core.resources.stickers.small_stickers import small_stickers_list


async def get_lesson(lesson_id: int, session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.id == lesson_id)
    result: Result = await session.execute(query)
    lesson = result.scalar()
    return lesson


async def get_lessons(session: AsyncSession) -> list[Lesson]:
    query = select(Lesson)
    result = await session.execute(query)
    lessons = result.scalars().all()
    return [row for row in lessons]


async def add_completed_lesson_to_db(user_id: int, lesson_id: int, session: AsyncSession) -> None:
    upsert_query = insert(UserCompleteLesson).values(user_id=user_id, lesson_id=lesson_id)
    upsert_query = upsert_query.on_conflict_do_nothing()
    await session.execute(upsert_query)


async def get_completed_lessons(user_id: int, session: AsyncSession) -> set[int]:
    query = select(UserCompleteLesson.lesson_id).filter(UserCompleteLesson.user_id == user_id)
    result = await session.execute(query)
    completed_lessons_ids = {row[0] for row in result.all()}
    return completed_lessons_ids


async def lesson_routine(bot: Bot,
                         user: User,
                         lesson_id: int,
                         slide_id: int,
                         state: FSMContext,
                         session: AsyncSession,
                         starts_from: StartsFrom = StartsFrom.BEGIN) -> None:
    slide = await get_slide_by_id(lesson_id=lesson_id, slide_id=slide_id, session=session)
    await update_session(user_id=user.id, lesson_id=lesson_id, current_slide_id=slide.id, session=session, starts_from=starts_from)
    match slide.slide_type:
        case SlideType.TEXT:
            text = slide.text
            if not slide.keyboard_type:
                await bot.send_message(chat_id=user.telegram_id, text=text)
                if slide.delay:
                    await asyncio.sleep(float(slide.delay))
                await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide,
                                     state=state, session=session)
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_id, next_slide=slide.next_slide)
                        await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'

        case SlideType.IMAGE:
            image_file = slide.picture
            path = f'core/resources/images/lesson{lesson_id}/{image_file}'
            if not slide.keyboard_type:
                await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=path))
                if slide.delay:
                    await asyncio.sleep(float(slide.delay))
                await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide,
                                     state=state, session=session)
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_id, next_slide=slide.next_slide)
                        await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=path), reply_markup=markup)
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'
        case SlideType.SMALL_STICKER:
            await bot.send_sticker(chat_id=user.telegram_id, sticker=get_random_sticker_id(collection=small_stickers_list))
            await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide,
                                 state=state, session=session)
        case SlideType.BIG_STICKER:
            # TODO: брать большой стикер из другой коллекции, когда она подъедет
            await bot.send_sticker(chat_id=user.telegram_id, sticker=get_random_sticker_id(collection=small_stickers_list))
            await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide,
                                 state=state, session=session)
        case SlideType.PIN_DICT:
            text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            await bot.pin_chat_message(chat_id=user.telegram_id, message_id=msg.message_id, disable_notification=True)
            await lesson_routine(bot=bot, user=user, lesson_id=lesson_id, slide_id=slide.next_slide,
                                 state=state, session=session)
        case SlideType.QUIZ_OPTIONS:
            text = slide.text
            answer = slide.right_answers
            options = sample(population=slide.keyboard.split('|'), k=3)
            markup = get_quiz_keyboard(words=options, answer=answer, lesson_id=lesson_id, slide_id=slide.id)
            msg = await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
            await state.update_data(quiz_options_msg_id=msg.message_id)
        case SlideType.QUIZ_INPUT_WORD:
            text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            await state.update_data(quiz_word_msg_id=msg.message_id,
                                    quiz_word_lesson_id=lesson_id,
                                    quiz_word_slide_id=slide_id)
            await state.set_state(States.INPUT_WORD)
        case SlideType.QUIZ_INPUT_PHRASE:
            text = slide.text
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            await state.update_data(quiz_phrase_msg_id=msg.message_id,
                                    quiz_phrase_lesson_id=lesson_id,
                                    quiz_phrase_slide_id=slide_id)
            await state.set_state(States.INPUT_PHRASE)
        case SlideType.FINAL_SLIDE:
            text = slide.text
            lesson = await get_lesson(lesson_id=lesson_id, session=session)
            await bot.send_message(chat_id=user.telegram_id, text=text)
            await bot.send_message(chat_id=user.telegram_id, text=f'Поздравляем, вы прошли урок {lesson.title}!')
            await bot.unpin_all_chat_messages(chat_id=user.telegram_id)
            await add_completed_lesson_to_db(user_id=user.id, lesson_id=lesson_id, session=session)
            await mark_lesson_as_completed(user_id=user.id, lesson_id=lesson_id, session=session)
            await state.clear()
            return
        case _:
            assert False, f'Unknown slide type: {slide.slide_type}'
