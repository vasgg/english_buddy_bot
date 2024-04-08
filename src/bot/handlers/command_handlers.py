from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommandScopeChat
from bot.controllers.user_controllers import propose_reminder_to_user, show_start_menu
from bot.internal.commands import special_commands
from config import get_settings
from database.crud.answer import get_text_by_prompt
from database.crud.user import toggle_user_paywall_access
from database.models.user import User
from enums import States
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()


@router.message(CommandStart())
async def start_message(
        message: types.Message,
        user: User,
        is_new_user: bool,
        db_session: AsyncSession,
        state: FSMContext,
) -> None:
    if message.from_user.id in get_settings().ADMINS:
        await message.bot.set_my_commands(special_commands, scope=BotCommandScopeChat(chat_id=message.from_user.id))
    await state.clear()
    if is_new_user:
        await propose_reminder_to_user(message, db_session=db_session)
        return
    await show_start_menu(message, user.id, db_session)


@router.message(Command('support'))
async def support_message(message: types.Message, db_session: AsyncSession) -> None:
    await message.answer(
        text=await get_text_by_prompt(prompt='support_text', db_session=db_session))


@router.message(Command('paywall'))
async def toggle_paywall_access(message: types.Message, user: User, db_session: AsyncSession) -> None:
    if message.from_user.id not in get_settings().ADMINS:
        return
    await toggle_user_paywall_access(user_id=user.id, db_session=db_session)
    await db_session.refresh(user)
    await message.answer(
        text=await get_text_by_prompt(prompt='access_status', db_session=db_session)
             + (' enabled' if user.paywall_access else ' disabled'),
    )


@router.message(Command('reminders'))
async def set_user_reminders(message: types.Message, db_session: AsyncSession) -> None:
    await propose_reminder_to_user(message, db_session)
