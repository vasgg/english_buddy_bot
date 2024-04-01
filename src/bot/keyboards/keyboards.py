from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.callback_data import (
    ExtraSlidesCallbackFactory,
    FurtherButtonCallbackFactory,
    HintCallbackFactory,
    LessonStartsFromCallbackFactory,
    LessonsCallbackFactory,
    QuizCallbackFactory,
    RemindersCallbackFactory,
    SlideCallbackFactory,
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


def get_furher_button(current_lesson: int, next_slide: int) -> InlineKeyboardMarkup:
    # переделать логику. мы не должны зависить от инфы извне. клавиатура ничего не знает!
    button = [
        [
            InlineKeyboardButton(
                text="Далее",
                # выкидываем метаданные.
                callback_data=SlideCallbackFactory(lesson_id=current_lesson, next_slide_id=next_slide).pack(),
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button)


def get_new_furher_button() -> InlineKeyboardMarkup:
    button = [
        [
            InlineKeyboardButton(
                text="Далее",
                callback_data=FurtherButtonCallbackFactory(further_requested=True).pack(),
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button)


def get_quiz_keyboard(words: list[str], answer: str, lesson_id: int, slide_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for word in words:
        if word == answer:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=word,
                        callback_data=QuizCallbackFactory(answer=word, lesson_id=lesson_id, slide_id=slide_id).pack(),
                    )
                ]
            )
        else:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=word,
                        callback_data=QuizCallbackFactory(
                            answer=f'wrong_answer|{word}',
                            lesson_id=lesson_id,
                            slide_id=slide_id,
                        ).pack(),
                    )
                ]
            )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_lesson_progress_keyboard(
    mode: UserLessonProgress,
    lesson: Lesson,
    exam_slide_id: int | None = None,
) -> InlineKeyboardMarkup:
    first_slide_id = lesson.path.split('.')[0]
    match mode:
        case UserLessonProgress.NO_PROGRESS:
            if exam_slide_id:
                buttons = [
                    [
                        InlineKeyboardButton(
                            text='Начать урок сначала',
                            callback_data=LessonStartsFromCallbackFactory(
                                lesson_id=lesson.id,
                                slide_id=first_slide_id,
                                attr=LessonStartsFrom.BEGIN,
                            ).pack(),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text='Начать с экзамена',
                            callback_data=LessonStartsFromCallbackFactory(
                                lesson_id=lesson.id,
                                slide_id=exam_slide_id,
                                attr=LessonStartsFrom.EXAM,
                            ).pack(),
                        )
                    ],
                ]
            else:
                buttons = [
                    [
                        InlineKeyboardButton(
                            text='Начать урок сначала',
                            callback_data=LessonStartsFromCallbackFactory(
                                lesson_id=lesson.id,
                                slide_id=first_slide_id,
                                attr=LessonStartsFrom.BEGIN,
                            ).pack(),
                        )
                    ]
                ]
        case UserLessonProgress.IN_PROGRESS:
            buttons = [
                [
                    InlineKeyboardButton(
                        text='Начать урок сначала',
                        callback_data=LessonStartsFromCallbackFactory(
                            lesson_id=lesson.id,
                            slide_id=first_slide_id,
                            attr=LessonStartsFrom.BEGIN,
                        ).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='Продолжить урок',
                        callback_data=LessonStartsFromCallbackFactory(
                            lesson_id=lesson.id,
                            attr=LessonStartsFrom.CONTINUE,
                        ).pack(),
                    )
                ],
            ]
        case _:
            assert False, f'Unknown mode: {mode}'
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_hint_keyaboard() -> InlineKeyboardMarkup:
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


def get_extra_slides_keyaboard() -> InlineKeyboardMarkup:
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
