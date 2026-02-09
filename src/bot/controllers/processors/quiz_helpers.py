import logging

import sentry_sdk
from aiogram import types

from bot.keyboards.keyboards import get_hint_keyboard
from database.crud.answer import get_text_by_prompt
from database.crud.session import get_wrong_answers_counter
from database.models.slide import Slide
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_missing_almost_right_answer_reply_reported: set[int] = set()


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


def _report_missing_almost_right_answer_reply(slide: Slide) -> None:
    if slide.id in _missing_almost_right_answer_reply_reported:
        return
    _missing_almost_right_answer_reply_reported.add(slide.id)

    slide_type = slide.slide_type.value if hasattr(slide.slide_type, 'value') else str(slide.slide_type)
    message = (
        'Slide has almost_right_answers but missing almost_right_answer_reply. '
        f'slide_id={slide.id} lesson_id={slide.lesson_id} slide_type={slide_type}'
    )
    logger.warning(message)

    with sentry_sdk.new_scope() as scope:
        scope.set_tag('slide_type', slide_type)
        scope.set_context('slide', {'slide_id': slide.id, 'lesson_id': slide.lesson_id, 'slide_type': slide_type})
        sentry_sdk.capture_message(message, level='warning')


async def answer_almost_right_reply(event: types.Message, slide: Slide, db_session: AsyncSession) -> None:
    reply = slide.almost_right_answer_reply
    if not reply or not str(reply).strip():
        _report_missing_almost_right_answer_reply(slide)
        try:
            reply = await get_text_by_prompt(prompt='missing_almost_right_answer_reply', db_session=db_session)
        except Exception:
            logger.exception(
                'Failed to load fallback text for prompt=%s. slide_id=%s',
                'missing_almost_right_answer_reply',
                slide.id,
            )
            reply = 'Почти правильно!'

    await event.answer(text=str(reply))
