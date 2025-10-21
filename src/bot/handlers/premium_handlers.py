from contextlib import suppress
from datetime import UTC, datetime
import logging

from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound
from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile, LabeledPrice, PreCheckoutQuery, Message
from aiogram.utils.media_group import MediaGroupBuilder
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.helpers import get_image_paths
from bot.keyboards.callback_data import PaymentSentCallbackFactory, PremiumSubDurationCallbackFactory
from bot.keyboards.keyboards import get_lesson_picker_keyboard
from config import get_settings
from database.crud.answer import get_text_by_prompt
from database.crud.lesson import get_active_lessons, get_completed_lessons_from_sessions
from database.models.user import User
from enums import SubscriptionType, SubscriptionDuration, UserSubscriptionType

logger = logging.Logger(__name__)

router = Router()


@router.pre_checkout_query()
async def on_pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery,
):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(
    message: Message,
    user: User,
    db_session: AsyncSession,
):
    payload = message.successful_payment.invoice_payload
    match payload:
        case SubscriptionDuration.ONE_MONTH:
            months = 1
            prompt = 'stars_payment_complete_1m'
        case SubscriptionDuration.THREE_MONTH:
            months = 3
            prompt = 'stars_payment_complete_3m'
        case _:
            assert False, f'Unexpected subscription type {payload}'
    today = datetime.now(UTC).date()
    if user.subscription_expired_at and user.subscription_expired_at > today:
        new_expiry = user.subscription_expired_at + relativedelta(months=months)
    else:
        new_expiry = today + relativedelta(months=months)
    user.subscription_status = UserSubscriptionType.LIMITED_ACCESS
    user.subscription_expired_at = new_expiry
    text = await get_text_by_prompt(prompt=prompt, db_session=db_session)
    await message.answer(text)
    logger.info(f"Successful payment for user {user.username}: {message.successful_payment.invoice_payload}")


@router.callback_query(PremiumSubDurationCallbackFactory.filter())
async def premium_types_message(
    callback: types.CallbackQuery, callback_data: PremiumSubDurationCallbackFactory
) -> None:
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete_reply_markup()
    match callback_data.duration:
        case SubscriptionDuration.ONE_MONTH:
            description = "Длительность: 1 месяц"
            prices = [
                LabeledPrice(label="Подписка на 1 месяц", amount=35),
            ]
        case SubscriptionDuration.THREE_MONTH:
            description = "Длительность: 3 месяца"
            prices = [
                LabeledPrice(label="Подписка на 3 месяца", amount=90),
            ]
        case _:
            assert False, f'Unexpected subscription type {callback_data.duration}'
    await callback.message.answer_invoice(
        title="Подписка",
        description=description,
        payload=callback_data.duration,
        currency="XTR",
        prices=prices,
        start_parameter="stars-payment",
    )


@router.callback_query(PaymentSentCallbackFactory.filter())
async def premium_payment_sent_message(
    callback: types.CallbackQuery, callback_data: PaymentSentCallbackFactory, user: User, db_session: AsyncSession
) -> None:
    await callback.answer()
    with suppress(TelegramBadRequest):
        await callback.message.delete_reply_markup()
    lessons = await get_active_lessons(db_session)
    completed_lessons = await get_completed_lessons_from_sessions(user_id=user.id, db_session=db_session)
    await callback.message.answer(
        text=await get_text_by_prompt(prompt='validating_process_text', db_session=db_session),
        reply_markup=get_lesson_picker_keyboard(lessons=lessons, completed_lessons=completed_lessons),
    )
    admin_message_text = await get_text_by_prompt(prompt='new_sub_admin_notify', db_session=db_session)
    user_info = f'{user.fullname} (@{user.username})' if user.username else user.fullname
    sub_type = 'monthly' if callback_data.subscription_type == SubscriptionType.LIMITED else 'alltime ⭐'
    for admin in get_settings().SUB_ADMINS:
        try:
            await callback.bot.send_message(
                chat_id=admin,
                text=admin_message_text.format(user_info, sub_type),
            )
        except (TelegramForbiddenError, TelegramNotFound) as exc:
            logger.warning("Unable to notify admin %s about new subscription: %s", admin, exc)


@router.callback_query(F.data == 'discount_button')
async def discount_button_callback_processing(
    callback: types.CallbackQuery,
    db_session: AsyncSession,
) -> None:
    await callback.answer()
    await callback.message.delete()
    image_paths = get_image_paths()
    caption = await get_text_by_prompt(prompt='discount_button_caption', db_session=db_session)
    if not image_paths:
        await callback.answer("Нет доступных изображений для репоста.")
        return

    media = MediaGroupBuilder(caption=caption)
    for path in image_paths:
        media.add_photo(media=FSInputFile(path))

    await callback.message.answer_media_group(media.build())


@router.message(Command("refund"))
async def cmd_refund(
    message: Message,
    bot: Bot,
    user: User,
    command: CommandObject,
):
    settings = get_settings()
    if message.from_user.id != settings.ADMIN:
        return
    transaction_id = command.args
    if transaction_id is None:
        await message.answer("No refund code provided")
        return
    try:
        await bot.refund_star_payment(user_id=message.from_user.id, telegram_payment_charge_id=transaction_id)
        await message.answer("Refund successful")
        logger.info(f"Refund for user {user.username} successful: {transaction_id}")
    except TelegramBadRequest as error:
        if "CHARGE_NOT_FOUND" in error.message:
            text = "Refund code not found"
        elif "CHARGE_ALREADY_REFUNDED" in error.message:
            text = "Stars already refunded"
        else:
            text = "Refund code not found"
        await message.answer(text)
        logger.exception(error.message)
        return
