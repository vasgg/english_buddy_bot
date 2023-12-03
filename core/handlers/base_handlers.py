from aiogram import Router, types
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import get_completed_lessons, get_lessons
from core.database.models import User
from core.keyboards.keyboards import get_lesson_picker_keyboard

router = Router()


@router.message(CommandStart())
async def start_message(message: types.Message, user: User, session: AsyncSession) -> None:
    lessons = await get_lessons(session)
    completed_lessons = await get_completed_lessons(user_id=user.id, session=session)
    await message.answer(text='<b>Вас приветствует <i>поли-бот</i>!</b>\n',
                         reply_markup=await get_lesson_picker_keyboard(lessons=lessons,
                                                                       completed_lessons=completed_lessons)) 
