from aiogram import types


async def process_dict(
    event: types.Message,
    text: str,
) -> bool:
    msg = await event.answer(text=text)
    await msg.pin(disable_notification=True)
    return True
