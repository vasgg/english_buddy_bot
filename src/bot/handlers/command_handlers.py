from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.user_controllers import propose_reminder_to_user, show_start_menu
from bot.keyboards.keyboards import get_premium_keyboard
from database.crud.answer import get_text_by_prompt
from database.models.user import User
from enums import UserSubscriptionType

router = Router()


@router.message(CommandStart())
async def start_message(
    message: types.Message,
    user: User,
    is_new_user: bool,
    db_session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()
    if is_new_user:
        await propose_reminder_to_user(message, db_session=db_session)
        return
    await show_start_menu(message, user.id, db_session)


@router.message(Command('premium'))
async def premium_message(message: types.Message, user: User, db_session: AsyncSession) -> None:
    await message.answer(
        text=await get_text_by_prompt(prompt='premium_text', db_session=db_session), reply_markup=get_premium_keyboard()
    )
    if user.subscription_status == UserSubscriptionType.NO_ACCESS:
        user.subscription_status = UserSubscriptionType.ACCESS_INFO_REQUESTED


@router.message(Command('reminders'))
async def set_user_reminders(message: types.Message, db_session: AsyncSession) -> None:
    await propose_reminder_to_user(message, db_session)
