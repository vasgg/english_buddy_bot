from aiogram import F, Router, types
from aiogram.filters import CommandStart

from core.keyboards.base_keyboards import lesson_picker

router = Router()


@router.message(CommandStart())
async def start_message(message: types.Message) -> None:
    await message.answer(text='<b>Вас приветствует <i>поли-бот</i>!</b>\n',
                         reply_markup=lesson_picker)

# TODO: вынести текст в переменные



