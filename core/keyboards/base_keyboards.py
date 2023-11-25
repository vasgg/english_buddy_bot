from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

start_keyboard = ReplyKeyboardMarkup(is_persistent=True,
                                     resize_keyboard=True,
                                     keyboard=[[KeyboardButton(text='📔 lessons')],
                                               [KeyboardButton(text='📖 start lesson from beginning')]])

lesson_picker = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='HE IS HAPPY', callback_data='lesson_1')],
        [InlineKeyboardButton(text='HE IS NOT HAPPY', callback_data='lesson_2')],
        [InlineKeyboardButton(text='IS HE HAPPY?', callback_data='lesson_3')],
        [InlineKeyboardButton(text='HE IS A STUDENT', callback_data='lesson_4')],
        [InlineKeyboardButton(text='COLORS AND OBJECTS', callback_data='lesson_5')],
    ]
)
