from aiogram import Router, types
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.lesson_controllers import get_completed_lessons, get_lessons
from bot.database.models.user import User
from bot.keyboards.keyboards import get_lesson_picker_keyboard

router = Router()


@router.message(CommandStart())
async def start_message(message: types.Message, user: User, db_session: AsyncSession) -> None:
    lessons = await get_lessons(db_session)
    completed_lessons = await get_completed_lessons(user_id=user.id, db_session=db_session)
    # TODO: перенести текста в базу
    await message.answer(
        text="<b>Вас приветствует <i>поли-бот</i>!</b>\n",
        reply_markup=await get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )
