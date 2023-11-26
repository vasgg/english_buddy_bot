from aiogram.filters.callback_data import CallbackData


class LessonsCallbackFactory(CallbackData, prefix='lesson'):
    lesson_number: int


class SlideCallbackFactory(CallbackData, prefix='slide'):
    lesson_number: int
    slide_number: int

