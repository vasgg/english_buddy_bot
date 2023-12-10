from aiogram import Bot

from core.config import settings


async def on_startup_notify(bot: Bot):
    await bot.send_message(settings.ADMINS[0], "Bot started", disable_notification=True)


async def on_shutdown_notify(bot: Bot):
    await bot.send_message(settings.ADMINS[0], "Bot shutdown", disable_notification=True)
