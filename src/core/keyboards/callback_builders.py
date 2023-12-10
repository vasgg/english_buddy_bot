from aiogram.filters.callback_data import CallbackData

from core.resources.enums import LessonStartsFrom


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
