from aiogram import Bot, types


async def set_bot_command(bot: Bot):
    bot_commands = [
        types.BotCommand(command="/start", description="start bot"),
    ]
    await bot.set_my_commands(bot_commands)
