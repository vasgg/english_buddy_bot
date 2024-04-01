from aiogram.filters.callback_data import CallbackData

from enums import LessonStartsFrom


class LessonsCallbackFactory(CallbackData, prefix='lesson'):
    lesson_id: int


class SlideCallbackFactory(CallbackData, prefix='slide'):
    lesson_id: int
    next_slide_id: int


class LessonStartsFromCallbackFactory(CallbackData, prefix='start_from'):
    lesson_id: int
    attr: LessonStartsFrom


class QuizCallbackFactory(CallbackData, prefix='quiz'):
    answer: str


class RemindersCallbackFactory(CallbackData, prefix='reminder'):
    frequency: int


class HintCallbackFactory(CallbackData, prefix='hint'):
    hint_requested: bool


class ExtraSlidesCallbackFactory(CallbackData, prefix='extra_slides'):
    extra_slides_requested: bool


class FurtherButtonCallbackFactory(CallbackData, prefix='further_button'):
    further_requested: bool
