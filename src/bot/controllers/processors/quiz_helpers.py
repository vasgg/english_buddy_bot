from aiogram import types
from bot.keyboards.keyboards import get_hint_keyboard
from database.crud.answer import get_text_by_prompt
from database.crud.session import get_wrong_answers_counter
from sqlalchemy.ext.asyncio import AsyncSession


async def show_hint_dialog(
    event: types.Message,
    db_session: AsyncSession,
):
    await event.answer(
        text=(await get_text_by_prompt(prompt='3_wrong_answers', db_session=db_session)),
        reply_markup=get_hint_keyboard(),
    )


async def error_count_exceeded(session_id: int, slide_id: int, db_session: AsyncSession) -> bool:
    wrong_answers_count = await get_wrong_answers_counter(session_id, slide_id, db_session)
    if wrong_answers_count >= 3:
        return True
    return False
