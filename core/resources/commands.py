from aiogram import Bot, types


async def set_bot_commands(bot: Bot) -> None:
    bot_commands = [
        types.BotCommand(command="/start", description="start bot"),
        types.BotCommand(command="/position", description="set slide position"),
    ]
    await bot.set_my_commands(bot_commands)
