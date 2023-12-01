from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Lesson
from core.keyboards.callback_builders import LessonsCallbackFactory, QuizCallbackFactory, SlideCallbackFactory, LessonStartFromCallbackFactory
from core.resources.enums import UserLessonProgress


async def get_lesson_picker_keyboard(lessons: list[Lesson], completed_lessons: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for lesson in lessons:
        if lesson.id in completed_lessons:
            buttons.append([InlineKeyboardButton(text=f'{lesson.title} ✅', callback_data=LessonsCallbackFactory(lesson_number=lesson.id).pack())])
        else:
            buttons.append([InlineKeyboardButton(text=lesson.title, callback_data=LessonsCallbackFactory(lesson_number=lesson.id).pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_furher_button(current_lesson: int, current_slide: int) -> InlineKeyboardMarkup:
    button = [[InlineKeyboardButton(text='Далее',
                                    callback_data=SlideCallbackFactory(lesson_number=current_lesson, slide_number=current_slide + 1).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=button)


def get_quiz_keyboard(words: list[str], answer: str, lesson_number: int, slide_number: int) -> InlineKeyboardMarkup:
    buttons = []
    for word in words:
        if word == answer:
            buttons.append([InlineKeyboardButton(text=word, callback_data=QuizCallbackFactory(answer=word,
                                                                                              lesson_number=lesson_number,
                                                                                              slide_number=slide_number).pack())])
        else:
            buttons.append([InlineKeyboardButton(text=word, callback_data=QuizCallbackFactory(answer='wrong',
                                                                                              lesson_number=lesson_number,
                                                                                              slide_number=slide_number).pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_lesson_progress_keyboard(mode: UserLessonProgress, lesson_number: int,
                                       session: AsyncSession, current_slide: int = None) -> InlineKeyboardMarkup:
    from core.controllers.lesson_controllers import get_lesson
    lesson = await get_lesson(lesson_number=lesson_number, session=session)
    match mode:
        case UserLessonProgress.NO_PROGRESS:
            buttons = [
                [InlineKeyboardButton(text='Начать урок сначала', callback_data=LessonStartFromCallbackFactory(lesson_number=lesson_number,
                                                                                                               slide_number=1).pack())],
                [InlineKeyboardButton(text='Начать с экзамена', callback_data=LessonStartFromCallbackFactory(lesson_number=lesson_number,
                                                                                                             slide_number=lesson.exam_slide).pack())],
            ]
            return InlineKeyboardMarkup(inline_keyboard=buttons)
        case UserLessonProgress.IN_PROGRESS:
            buttons = [
                [InlineKeyboardButton(text='Начать урок сначала', callback_data=LessonStartFromCallbackFactory(lesson_number=lesson_number,
                                                                                                               slide_number=1).pack())],
                [InlineKeyboardButton(text='Продолжить урок', callback_data=LessonStartFromCallbackFactory(lesson_number=lesson_number,
                                                                                                           slide_number=current_slide).pack())],
            ]
            return InlineKeyboardMarkup(inline_keyboard=buttons)
