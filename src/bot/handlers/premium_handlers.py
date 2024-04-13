import logging

from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.callback_data import PaymentSentCallbackFactory, PremiumSubCallbackFactory
from bot.keyboards.keyboards import get_lesson_picker_keyboard, get_payment_sent_keyboard
from config import get_settings
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import get_completed_lessons_from_sessions, get_lessons
from database.models.user import User
from enums import SubscriptionType

logger = logging.Logger(__name__)

router = Router()


@router.callback_query(PremiumSubCallbackFactory.filter())
async def premium_types_message(
    callback: types.CallbackQuery, callback_data: PremiumSubCallbackFactory, db_session: AsyncSession
) -> None:
    await callback.answer()
    await callback.message.delete_reply_markup()
    match callback_data.subscription_type:
        case SubscriptionType.LIMITED:
            await callback.message.answer(
                text=await get_text_by_prompt(prompt='monthly_premium_text', db_session=db_session),
                reply_markup=get_payment_sent_keyboard(mode=SubscriptionType.LIMITED),
            )
        case SubscriptionType.ALLTIME:
            await callback.message.answer(
                text=await get_text_by_prompt(prompt='alltime_premium_text', db_session=db_session),
                reply_markup=get_payment_sent_keyboard(mode=SubscriptionType.ALLTIME),
            )
        case _:
            assert False, f'Unexpected subscription type {callback_data.subscription_type}'


@router.callback_query(PaymentSentCallbackFactory.filter())
async def premium_payment_sent_message(
    callback: types.CallbackQuery, callback_data: PaymentSentCallbackFactory, user: User, db_session: AsyncSession
) -> None:
    await callback.answer()
    await callback.message.delete_reply_markup()
    lessons = await get_lessons(db_session)
    completed_lessons = await get_completed_lessons_from_sessions(user_id=user.id, db_session=db_session)
    await callback.message.answer(
        text=await get_text_by_prompt(prompt='validating_process_text', db_session=db_session),
        reply_markup=get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )
    admin_message_text = await get_text_by_prompt(prompt='new_sub_admin_notify', db_session=db_session)
    user_info = f'{user.fullname} (@{user.username})' if user.username else user.fullname
    sub_type = 'monthly' if callback_data.subscription_type == SubscriptionType.LIMITED else 'alltime ⭐'
    await callback.bot.send_message(
        chat_id=get_settings().SUB_ADMINS[0],
        text=admin_message_text.format(user_info, sub_type),
    )
