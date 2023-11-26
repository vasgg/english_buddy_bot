from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from core.keyboards.callback_builders import LessonsCallbackFactory

lesson_picker = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='HE IS HAPPY', callback_data=LessonsCallbackFactory(lesson_number=1).pack())],
        [InlineKeyboardButton(text='HE IS NOT HAPPY', callback_data=LessonsCallbackFactory(lesson_number=2).pack())],
        [InlineKeyboardButton(text='IS HE HAPPY?', callback_data=LessonsCallbackFactory(lesson_number=3).pack())],
        [InlineKeyboardButton(text='HE IS A STUDENT', callback_data=LessonsCallbackFactory(lesson_number=4).pack())],
        [InlineKeyboardButton(text='COLORS AND OBJECTS', callback_data=LessonsCallbackFactory(lesson_number=5).pack())],
    ]
)
