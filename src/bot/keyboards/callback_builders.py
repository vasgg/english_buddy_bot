from aiogram.filters.callback_data import CallbackData

from bot.resources.enums import LessonStartsFrom


class LessonsCallbackFactory(CallbackData, prefix="lesson"):
    lesson_id: int


class SlideCallbackFactory(CallbackData, prefix="slide"):
    lesson_id: int
    next_slide_id: int


class LessonStartsFromCallbackFactory(CallbackData, prefix="start_from"):
    lesson_id: int
    slide_id: int
    attr: LessonStartsFrom


class QuizCallbackFactory(CallbackData, prefix="quiz"):
    lesson_id: int
    slide_id: int
    answer: str


class HintCallbackFactory(CallbackData, prefix="hint"):
    lesson_id: int
    slide_id: int
    payload: str


class RemindersCallbackFactory(CallbackData, prefix="reminder"):
    frequency: int
