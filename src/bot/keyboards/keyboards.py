from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.callback_data import (
    ExtraSlidesCallbackFactory,
    FurtherButtonCallbackFactory,
    HintCallbackFactory,
    LessonStartsFromCallbackFactory,
    LessonsCallbackFactory,
    QuizCallbackFactory,
    RemindersCallbackFactory,
)
from database.models.lesson import Lesson
from enums import LessonStartsFrom, UserLessonProgress


def get_lesson_picker_keyboard(lessons: list[Lesson], completed_lessons: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for lesson in lessons:
        mark = ' ✅' if lesson.id in completed_lessons else ''
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f'{lesson.title}{mark}',
                    callback_data=LessonsCallbackFactory(lesson_id=lesson.id).pack(),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_further_button() -> InlineKeyboardMarkup:
    button = [
        [
            InlineKeyboardButton(
                text="Далее",
                callback_data=FurtherButtonCallbackFactory(further_requested=True).pack(),
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button)


def get_quiz_keyboard(words: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for word in words:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=word,
                    callback_data=QuizCallbackFactory(text=word).pack(),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_lesson_progress_keyboard(
    mode: UserLessonProgress, lesson: Lesson, has_exam_slides: bool
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text='Начать урок сначала',
                callback_data=LessonStartsFromCallbackFactory(
                    lesson_id=lesson.id,
                    attr=LessonStartsFrom.BEGIN,
                ).pack(),
            )
        ]
    ]
    match mode:
        case UserLessonProgress.NO_PROGRESS:
            if has_exam_slides:
                buttons.append(
                    [
                        [
                            InlineKeyboardButton(
                                text='Начать с экзамена',
                                callback_data=LessonStartsFromCallbackFactory(
                                    lesson_id=lesson.id,
                                    attr=LessonStartsFrom.EXAM,
                                ).pack(),
                            )
                        ],
                    ]
                )
        case UserLessonProgress.IN_PROGRESS:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text='Продолжить урок',
                        callback_data=LessonStartsFromCallbackFactory(
                            lesson_id=lesson.id,
                            attr=LessonStartsFrom.CONTINUE,
                        ).pack(),
                    )
                ]
            )
        case _:
            assert False, f'Unknown mode: {mode}'
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_hint_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Подсказка',
                    callback_data=HintCallbackFactory(hint_requested=True).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Продолжить',
                    callback_data=HintCallbackFactory(hint_requested=False).pack(),
                )
            ],
        ]
    )


def get_extra_slides_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Да',
                    callback_data=ExtraSlidesCallbackFactory(show_extra_slides=True).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Нет',
                    callback_data=ExtraSlidesCallbackFactory(show_extra_slides=False).pack(),
                )
            ],
        ]
    )


def get_notified_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Каждый день',
                    callback_data=RemindersCallbackFactory(
                        frequency=1,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Раз в 3 дня',
                    callback_data=RemindersCallbackFactory(
                        frequency=3,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Раз в неделю',
                    callback_data=RemindersCallbackFactory(
                        frequency=7,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text='Не получать уведомления',
                    callback_data=RemindersCallbackFactory(
                        frequency=0,
                    ).pack(),
                )
            ],
        ]
    )
