from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.callback_data import (
    ExtraSlidesCallbackFactory,
    HintCallbackFactory,
    LessonStartsFromCallbackFactory,
    LessonsCallbackFactory,
    PaymentSentCallbackFactory,
    PremiumSubCallbackFactory,
    QuizCallbackFactory,
    RemindersCallbackFactory,
)
from database.models.lesson import Lesson
from enums import LessonStartsFrom, LessonStatus, SubscriptionType, UserLessonProgress


def get_lesson_picker_keyboard(lessons: list[Lesson], completed_lessons: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for lesson in lessons:
        editing_mark = '🧑‍🏫 ' if lesson.is_active == LessonStatus.EDITING else ''
        completion_mark = ' ✅' if lesson.id in completed_lessons else ''
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f'{editing_mark}{lesson.title}{completion_mark}',
                    callback_data=LessonsCallbackFactory(lesson_id=lesson.id).pack(),
                ),
            ],
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_further_button() -> InlineKeyboardMarkup:
    button = [
        [
            InlineKeyboardButton(
                text="Далее",
                callback_data='further_button',
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=button)


def get_quiz_keyboard(words: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for word in words:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=word,
                    callback_data=QuizCallbackFactory(answer=word).pack(),
                ),
            ],
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_lesson_progress_keyboard(
    mode: UserLessonProgress,
    lesson: Lesson,
    has_exam_slides: bool,
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text='Начать урок сначала',
                callback_data=LessonStartsFromCallbackFactory(
                    lesson_id=lesson.id,
                    attr=LessonStartsFrom.BEGIN,
                ).pack(),
            ),
        ],
    ]
    match mode:
        case UserLessonProgress.NO_PROGRESS:
            if has_exam_slides:
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text='Начать с экзамена',
                            callback_data=LessonStartsFromCallbackFactory(
                                lesson_id=lesson.id,
                                attr=LessonStartsFrom.EXAM,
                            ).pack(),
                        ),
                    ],
                )
        case UserLessonProgress.IN_PROGRESS:
            buttons.extend(
                [
                    [
                        InlineKeyboardButton(
                            text='Начать с экзамена',
                            callback_data=LessonStartsFromCallbackFactory(
                                lesson_id=lesson.id,
                                attr=LessonStartsFrom.EXAM,
                            ).pack(),
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text='Продолжить урок',
                            callback_data=LessonStartsFromCallbackFactory(
                                lesson_id=lesson.id,
                                attr=LessonStartsFrom.CONTINUE,
                            ).pack(),
                        ),
                    ],
                ]
            )
        case _:
            msg = f'Unknown mode: {mode}'
            raise AssertionError(msg)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_hint_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Подсказка',
                    callback_data=HintCallbackFactory(hint_requested=True).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Продолжить',
                    callback_data=HintCallbackFactory(hint_requested=False).pack(),
                ),
            ],
        ],
    )


def get_extra_slides_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Да',
                    callback_data=ExtraSlidesCallbackFactory(extra_slides_requested=True).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Нет',
                    callback_data=ExtraSlidesCallbackFactory(extra_slides_requested=False).pack(),
                ),
            ],
        ],
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
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Раз в 3 дня',
                    callback_data=RemindersCallbackFactory(
                        frequency=3,
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Раз в неделю',
                    callback_data=RemindersCallbackFactory(
                        frequency=7,
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Не получать уведомления',
                    callback_data=RemindersCallbackFactory(
                        frequency=0,
                    ).pack(),
                ),
            ],
        ],
    )


def get_premium_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Доступ на месяц',
                    callback_data=PremiumSubCallbackFactory(subscription_type=SubscriptionType.LIMITED).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text='Доступ навсегда',
                    callback_data=PremiumSubCallbackFactory(subscription_type=SubscriptionType.ALLTIME).pack(),
                ),
            ],
        ],
    )


def get_payment_sent_keyboard(mode: SubscriptionType) -> InlineKeyboardMarkup:
    sub_type = SubscriptionType.LIMITED if mode == SubscriptionType.LIMITED else SubscriptionType.ALLTIME
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Платёж отправлен',
                    callback_data=PaymentSentCallbackFactory(subscription_type=sub_type).pack(),
                ),
            ],
        ],
    )
