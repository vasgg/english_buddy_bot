from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.keyboards.callback_builders import SlideCallbackFactory


def get_furher_button(current_lesson: int, current_slide: int) -> InlineKeyboardMarkup:
    furter_button_builder = InlineKeyboardBuilder()
    furter_button_builder.button(text='Далее', callback_data=SlideCallbackFactory(lesson_number=current_lesson,
                                                                                  slide_number=current_slide + 1))
    # furter_button_builder.adjust(1)
    return furter_button_builder.as_markup()


def get_quiz_keyboard(current_lesson: int, current_slide: int) -> InlineKeyboardBuilder:
    ...
