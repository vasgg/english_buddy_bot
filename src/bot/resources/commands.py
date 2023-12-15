from aiogram import Bot, types

default_commands = [
    types.BotCommand(command="/start", description="start bot"),
]

special_commands = [
    types.BotCommand(command="/start", description="start bot"),
    types.BotCommand(command="/position", description="set slide position"),
    types.BotCommand(command="/paywall", description="toggle paywall access"),
]


async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(default_commands)
