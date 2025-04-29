from aiogram.filters.callback_data import CallbackData

from enums import LessonStartsFrom, SubscriptionType, SubscriptionDuration


class LessonsCallbackFactory(CallbackData, prefix='lesson'):
    lesson_id: int


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


class PremiumSubCallbackFactory(CallbackData, prefix='premium'):
    subscription_type: SubscriptionType


class PremiumSubDurationCallbackFactory(CallbackData, prefix='premium_duration'):
    duration: SubscriptionDuration

class PaymentSentCallbackFactory(CallbackData, prefix='payment_sent'):
    subscription_type: SubscriptionType
