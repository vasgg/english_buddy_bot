from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.models.lesson import Lesson
from bot.keyboards.callback_builders import (
    HintCallbackFactory,
    LessonStartsFromCallbackFactory,
    LessonsCallbackFactory,
    QuizCallbackFactory,
    SlideCallbackFactory,
)
from bot.resources.enums import LessonStartsFrom, UserLessonProgress


async def get_lesson_picker_keyboard(lessons: list[Lesson], completed_lessons: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for lesson in lessons:
        mark = " ✅" if lesson.id in completed_lessons else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{lesson.title}{mark}",
                    callback_data=LessonsCallbackFactory(lesson_id=lesson.id).pack(),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_furher_button(current_lesson: int, next_slide: int) -> InlineKeyboardMarkup:
    button = [
        [
            InlineKeyboardButton(
                text="Далее",
                callback_data=SlideCallbackFactory(lesson_id=current_lesson, next_slide_id=next_slide).pack(),
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
                            answer=f"wrong_answer {word}",
                            lesson_id=lesson_id,
                            slide_id=slide_id,
                        ).pack(),
                    )
                ]
            )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_lesson_progress_keyboard(
    mode: UserLessonProgress, lesson: Lesson, current_slide_id: int = None
) -> InlineKeyboardMarkup:
    match mode:
        case UserLessonProgress.NO_PROGRESS:
            buttons = [
                [
                    InlineKeyboardButton(
                        text="Начать урок сначала",
                        callback_data=LessonStartsFromCallbackFactory(
                            lesson_id=lesson.id,
                            slide_id=lesson.first_slide_id,
                            attr=LessonStartsFrom.BEGIN,
                        ).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Начать с экзамена",
                        callback_data=LessonStartsFromCallbackFactory(
                            lesson_id=lesson.id,
                            slide_id=lesson.exam_slide_id,
                            attr=LessonStartsFrom.EXAM,
                        ).pack(),
                    )
                ],
            ]
        case UserLessonProgress.IN_PROGRESS:
            assert current_slide_id
            buttons = [
                [
                    InlineKeyboardButton(
                        text="Начать урок сначала",
                        callback_data=LessonStartsFromCallbackFactory(
                            lesson_id=lesson.id,
                            slide_id=lesson.first_slide_id,
                            attr=LessonStartsFrom.BEGIN,
                        ).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Продолжить урок",
                        callback_data=LessonStartsFromCallbackFactory(
                            lesson_id=lesson.id,
                            slide_id=current_slide_id,
                            attr=LessonStartsFrom.CONTINUE,
                        ).pack(),
                    )
                ],
            ]
        case _:
            assert False, f"Unknown mode: {mode}"
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_hint_keyaboard(session_id: int, slide_id: int, lesson_id: int, right_answer: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подсказка",
                    callback_data=HintCallbackFactory(
                        session_id=session_id,
                        lesson_id=lesson_id,
                        slide_id=slide_id,
                        answer="show_hint",
                        right_answer=right_answer,
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Продолжить",
                    callback_data=HintCallbackFactory(
                        session_id=session_id,
                        lesson_id=lesson_id,
                        slide_id=slide_id,
                        answer="continue_button",
                        right_answer=right_answer,
                    ).pack(),
                )
            ],
        ]
    )
