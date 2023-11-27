from aiogram.filters.callback_data import CallbackData


class LessonsCallbackFactory(CallbackData, prefix='lesson'):
    lesson_number: int


class SlideCallbackFactory(CallbackData, prefix='slide'):
    lesson_number: int
    slide_number: int


class QuizCallbackFactory(CallbackData, prefix='quiz'):
    lesson_number: int
    slide_number: int
    answer: str
