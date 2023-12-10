from aiogram import Bot, types
from aiogram.types import BotCommandScopeChat

from core.config import settings

default_commands = [
    types.BotCommand(command="/start", description="start bot"),
]

special_commands = [
    types.BotCommand(command="/start", description="start bot"),
    types.BotCommand(command="/position", description="set slide position"),
]


async def set_bot_commands(bot: Bot) -> None:
    for user_id in settings.ADMINS:
        await bot.set_my_commands(special_commands, scope=BotCommandScopeChat(user_id))

    await bot.set_my_commands(bot_commands)


# Устанавливаем команды для всех остальных пользователей
await bot.set_my_commands(default_commands, scope=BotCommandScopeDefault())
