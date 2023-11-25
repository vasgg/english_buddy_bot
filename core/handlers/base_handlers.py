from aiogram import F, Router, types
from aiogram.filters import CommandStart

from core.keyboards.base_keyboards import lesson_picker, start_keyboard

router = Router()


@router.message(CommandStart())
async def start_message(message: types.Message) -> None:
    await message.answer(text='<b>Вас приветствует <i>поли-бот</i>!</b>\n'
                              'Горячие кнопки:\n\n'
                              '📔 <b>lessons</b> — посмотреть доступные уроки в рамках выбранного уровня знания английского\n'
                              '📖 <b>start lesson from beginning</b> — начать текущий урок с начала',
                         reply_markup=start_keyboard)


@router.message(F.text == '📔 lessons')
async def lessons_button_handler(message: types.Message) -> None:
    await message.answer(text='Выберите урок', reply_markup=lesson_picker)


@router.message(F.text == '📖 start lesson from beginning')
async def start_lesson_from_beginning_button_handler(message: types.Message) -> None:
    ...
