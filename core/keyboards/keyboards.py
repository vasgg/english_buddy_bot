from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Lesson
from core.keyboards.callback_builders import LessonStartsFromCallbackFactory, LessonsCallbackFactory, QuizCallbackFactory, SlideCallbackFactory
from core.resources.enums import LessonStartsFrom, UserLessonProgress


async def get_lesson_picker_keyboard(lessons: list[Lesson], completed_lessons: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for lesson in lessons:
        if lesson.id in completed_lessons:
            buttons.append([InlineKeyboardButton(text=f'{lesson.title} ✅',
                                                 callback_data=LessonsCallbackFactory(lesson_id=lesson.id).pack())])
        else:
            buttons.append([InlineKeyboardButton(text=lesson.title,
                                                 callback_data=LessonsCallbackFactory(lesson_id=lesson.id).pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_furher_button(current_lesson: int, next_slide: int) -> InlineKeyboardMarkup:
    button = [[InlineKeyboardButton(text='Далее',
                                    callback_data=SlideCallbackFactory(lesson_id=current_lesson, next_slide_id=next_slide).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=button)


def get_quiz_keyboard(words: list[str], answer: str, lesson_id: int, slide_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for word in words:
        if word == answer:
            buttons.append([InlineKeyboardButton(text=word, callback_data=QuizCallbackFactory(answer=word,
                                                                                              lesson_id=lesson_id,
                                                                                              slide_id=slide_id).pack())])
        else:
            buttons.append([InlineKeyboardButton(text=word, callback_data=QuizCallbackFactory(answer=f'wrong_answer {word}',
                                                                                              lesson_id=lesson_id,
                                                                                              slide_id=slide_id).pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_lesson_progress_keyboard(mode: UserLessonProgress, lesson_id: int,
                                       session: AsyncSession, current_slide: int = None) -> InlineKeyboardMarkup:
    from core.controllers.lesson_controllers import get_lesson
    lesson = await get_lesson(lesson_id=lesson_id, db_session=session)
    match mode:
        case UserLessonProgress.NO_PROGRESS:
            buttons = [
                [InlineKeyboardButton(text='Начать урок сначала', callback_data=LessonStartsFromCallbackFactory(lesson_id=lesson_id,
                                                                                                                slide_id=lesson.first_slide_id,
                                                                                                                attr=LessonStartsFrom.BEGIN).pack())],
                [InlineKeyboardButton(text='Начать с экзамена', callback_data=LessonStartsFromCallbackFactory(lesson_id=lesson_id,
                                                                                                              slide_id=lesson.exam_slide_id,
                                                                                                              attr=LessonStartsFrom.EXAM).pack())],
            ]
            return InlineKeyboardMarkup(inline_keyboard=buttons)
        case UserLessonProgress.IN_PROGRESS:
            buttons = [
                [InlineKeyboardButton(text='Начать урок сначала', callback_data=LessonStartsFromCallbackFactory(lesson_id=lesson_id,
                                                                                                                slide_id=lesson.first_slide_id,
                                                                                                                attr=LessonStartsFrom.BEGIN).pack())],
                [InlineKeyboardButton(text='Продолжить урок', callback_data=LessonStartsFromCallbackFactory(lesson_id=lesson_id,
                                                                                                            slide_id=current_slide,
                                                                                                            attr=LessonStartsFrom.CONTINUE).pack())],
            ]
            return InlineKeyboardMarkup(inline_keyboard=buttons)
