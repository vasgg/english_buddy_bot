from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_further_button(current_slide: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Далее', callback_data=f'next_slide_{current_slide + 1}')],
        ]
    )
