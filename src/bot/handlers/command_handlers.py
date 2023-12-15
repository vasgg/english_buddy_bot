from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommandScopeChat
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.controllers.session_controller import get_last_session_with_progress, get_session
from bot.controllers.user_controllers import propose_reminder_to_user, show_start_menu, toggle_user_paywall_access
from bot.database.models.user import User
from bot.handlers.lesson_handlers import common_processing
from bot.resources.commands import special_commands
from bot.resources.enums import States

router = Router()


@router.message(CommandStart())
async def start_message(
    message: types.Message, user: User, is_new_user: bool, db_session: AsyncSession, state: FSMContext
) -> None:
    if message.from_user.id in settings.ADMINS:
        await message.bot.set_my_commands(special_commands, scope=BotCommandScopeChat(chat_id=message.from_user.id))
    await state.clear()
    if is_new_user:
        await propose_reminder_to_user(message)
        return
    await show_start_menu(user=user, message=message, db_session=db_session)


@router.message(Command("position"))
async def set_slide_position(message: types.Message, user: User, state: FSMContext, db_session: AsyncSession) -> None:
    if message.from_user.id not in settings.ADMINS:
        return
    current_session = await get_last_session_with_progress(user_id=user.id, db_session=db_session)
    if not current_session:
        await message.answer(text="Please start session first")
        return
    await message.answer(text="Please enter target slide id")
    await state.update_data(custom_session_id=current_session.id)
    await state.set_state(States.INPUT_CUSTOM_SLIDE_ID)


@router.message(States.INPUT_CUSTOM_SLIDE_ID)
async def set_slide_position_handler(
    message: types.Message, state: FSMContext, bot: Bot, user: User, db_session: AsyncSession
) -> None:
    data = await state.get_data()
    session = await get_session(data["custom_session_id"], db_session)
    try:
        new_slide_id = int(message.text)
        await state.set_state()
        await common_processing(
            bot=bot,
            user=user,
            lesson_id=session.lesson_id,
            slide_id=new_slide_id,
            state=state,
            session=session,
            db_session=db_session,
        )
    except ValueError:
        await message.answer(text="Please provide correct slide id (integer)")
    except IntegrityError:
        await message.answer(text="Cant set slide position. Provided slide id does not exist")


@router.message(Command("paywall"))
async def toggle_paywall_access(message: types.Message, user: User, db_session: AsyncSession) -> None:
    if message.from_user.id not in settings.ADMINS:
        return
    await toggle_user_paywall_access(user_id=user.id, db_session=db_session)
    await db_session.refresh(user)
    await message.answer(
        text="Your current paywall access status: " + ("enabled" if user.paywall_access else "disabled"),
    )


@router.message(Command("reminders"))
async def set_user_reminders(message: types.Message) -> None:
    await propose_reminder_to_user(message)
