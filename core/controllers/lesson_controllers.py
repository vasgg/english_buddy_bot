import asyncio
from random import sample
from typing import Sequence

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.slide_controllers import get_slide
from core.controllers.user_controllers import delete_user_progress, update_user_progress
from core.database.models import Lesson, User, UserCompleteLesson
from core.keyboards.keyboards import get_furher_button, get_quiz_keyboard
from core.resources.enums import KeyboardType, SlideType, States


async def get_lesson(lesson_number: int, session: AsyncSession) -> Lesson:
    query = select(Lesson).filter(Lesson.id == lesson_number)
    result: Result = await session.execute(query)
    lesson = result.scalar()
    return lesson


async def get_lessons(session: AsyncSession) -> list[Lesson]:
    query = select(Lesson)
    result = await session.execute(query)
    lessons = result.scalars().all()
    return [row for row in lessons]


async def add_completed_lesson_to_db(user_id: int, lesson_number: int, session: AsyncSession) -> None:
    competed_lesson = UserCompleteLesson(user_id=user_id, lesson_id=lesson_number)
    session.add(competed_lesson)
    await session.flush()


async def get_completed_lessons(user_id: int, session: AsyncSession) -> set[int]:
    query = select(UserCompleteLesson.lesson_id).filter(UserCompleteLesson.user_id == user_id)
    result = await session.execute(query)
    completed_lessons_ids = {row[0] for row in result.all()}
    return completed_lessons_ids


async def lesson_routine(bot: Bot,
                         user: User,
                         lesson_number: int,
                         current_slide: int,
                         slide_amount: int,
                         state: FSMContext,
                         session: AsyncSession) -> None:
    if current_slide > slide_amount:
        lesson = await get_lesson(lesson_number=lesson_number, session=session)
        await bot.send_message(chat_id=user.telegram_id, text=f'Поздравляем, вы прошли урок {lesson.title}')
        await add_completed_lesson_to_db(user_id=user.id, lesson_number=lesson_number, session=session)
        await delete_user_progress(user_id=user.id, lesson_number=lesson_number, session=session)
        return
    slide = await get_slide(lesson_number=lesson_number, slide_number=current_slide, session=session)
    await update_user_progress(user_id=user.id, lesson_number=lesson_number, current_slide=slide.id, session=session)
    match slide.slide_type:
        case SlideType.TEXT:
            text = slide.text
            if not slide.keyboard_type:
                await bot.send_message(chat_id=user.telegram_id, text=text)
                if slide.delay:
                    await asyncio.sleep(int(slide.delay))
                await lesson_routine(bot=bot, user=user, lesson_number=lesson_number, current_slide=current_slide + 1,
                                     slide_amount=slide_amount, state=state, session=session)
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_number, current_slide=current_slide)
                        await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'

        case SlideType.IMAGE:
            image_file = slide.picture
            path = f'core/resources/images/lesson{lesson_number}/{image_file}'
            if not slide.keyboard_type:
                await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=path))
                if slide.delay:
                    await asyncio.sleep(int(slide.delay))
                await lesson_routine(bot=bot, user=user, lesson_number=lesson_number, current_slide=current_slide + 1,
                                     slide_amount=slide_amount, state=state, session=session)
            else:
                match slide.keyboard_type:
                    case KeyboardType.FURTHER:
                        markup = get_furher_button(current_lesson=lesson_number, current_slide=current_slide)
                        await bot.send_photo(chat_id=user.telegram_id, photo=types.FSInputFile(path=path), reply_markup=markup)
                    case _:
                        assert False, f'Unknown keyboard type: {slide.keyboard_type}'
        case SlideType.STICKER:
            ...
        case SlideType.QUIZ_OPTIONS:
            text = slide.text
            answer = slide.right_answers
            options = sample(population=slide.keyboard.split('|'), k=3)
            # TODO: тут мы смотрим на id слайда, без возможности изменить порядок. Надо будет переделать
            markup = get_quiz_keyboard(words=options, answer=answer, lesson_number=lesson_number, slide_number=slide.id)
            msg = await bot.send_message(chat_id=user.telegram_id, text=text, reply_markup=markup)
            quiz_options_msg_id = msg.message_id
            await state.update_data(quiz_options_msg_id=quiz_options_msg_id)
        case SlideType.QUIZ_INPUT_WORD:
            text = slide.text
            slide_number = slide.id
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            quiz_word_msg_id = msg.message_id
            await state.update_data(quiz_word_msg_id=quiz_word_msg_id,
                                    quiz_word_lesson_number=lesson_number,
                                    quiz_word_slide_number=slide_number)
            await state.set_state(States.INPUT_WORD)
        case SlideType.QUIZ_INPUT_PHRASE:
            text = slide.text
            slide_number = slide.id
            msg = await bot.send_message(chat_id=user.telegram_id, text=text)
            quiz_phrase_msg_id = msg.message_id
            await state.update_data(quiz_phrase_msg_id=quiz_phrase_msg_id,
                                    quiz_phrase_lesson_number=lesson_number,
                                    quiz_phrase_slide_number=slide_number)
            await state.set_state(States.INPUT_PHRASE)
        case _:
            assert False, f'Unknown slide type: {slide.slide_type}'
