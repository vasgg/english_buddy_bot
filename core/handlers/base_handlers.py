from aiogram import Router, types
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def start_message(message: types.Message) -> None:
    await message.answer(text='Hello, I am bot')
