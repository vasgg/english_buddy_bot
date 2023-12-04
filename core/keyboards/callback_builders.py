from aiogram.filters.callback_data import CallbackData


class LessonsCallbackFactory(CallbackData, prefix='lesson'):
    lesson_id: int


class SlideCallbackFactory(CallbackData, prefix='slide'):
    lesson_id: int
    next_slide_id: int


class LessonStartFromCallbackFactory(CallbackData, prefix='start_from'):
    lesson_id: int
    slide_id: int


class QuizCallbackFactory(CallbackData, prefix='quiz'):
    lesson_id: int
    slide_id: int
    answer: str


