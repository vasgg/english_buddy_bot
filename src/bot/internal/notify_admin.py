from aiogram import Bot

from config import get_settings


async def on_startup_notify(bot: Bot):
    await bot.send_message(get_settings().ADMINS[0], 'Bot started', disable_notification=True)


async def on_shutdown_notify(bot: Bot):
    await bot.send_message(get_settings().ADMINS[0], 'Bot shutdown', disable_notification=True)
