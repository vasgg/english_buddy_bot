from aiogram import Bot

from config import get_settings


async def on_startup_notify(bot: Bot):
    bot_info = await bot.get_me()
    await bot.send_message(
        get_settings().ADMIN,
        f'{bot_info.username} started\n\n/start',
        disable_notification=True,
    )


async def on_shutdown_notify(bot: Bot):
    bot_info = await bot.get_me()
    await bot.send_message(
        get_settings().ADMIN,
        f'{bot_info.username} shutdown',
        disable_notification=True,
    )
