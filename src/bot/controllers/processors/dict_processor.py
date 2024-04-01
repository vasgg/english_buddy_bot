from aiogram import types


async def process_dict(
    event: types.Message,
    text: str,
) -> bool:
    msg = await event.answer(text=text)
    await event.bot.pin_chat_message(
        chat_id=event.from_user.id,
        message_id=msg.message_id,
        disable_notification=True,
    )
    return True

