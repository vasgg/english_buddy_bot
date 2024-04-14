import logging

from contextlib import asynccontextmanager
from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.controllers.final_controllers import finalizing, finalizing_extra
from bot.controllers.processors.dict_processor import process_dict
from bot.controllers.processors.image_processor import process_image
from bot.controllers.processors.input_models import UserQuizInput
from bot.controllers.processors.quiz_input_phrase_processor import process_quiz_input_phrase
from bot.controllers.processors.quiz_input_word_processor import process_quiz_input_word
from bot.controllers.processors.quiz_options_processor import process_quiz_options
from bot.controllers.processors.sticker_processor import process_sticker
from bot.controllers.processors.text_processor import process_text
from database.crud.slide import get_slide_by_id
from database.models.session import Session
from database.models.slide import Slide
from enums import SlideType
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def process_slide(
    event: types.Message,
    state: FSMContext,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
    user_input: UserQuizInput | None,
) -> bool:
    match slide.slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            return await process_sticker(event, slide.slide_type, db_session)
        case SlideType.TEXT:
            return await process_text(event, slide)
        case SlideType.IMAGE:
            return await process_image(event, slide, session)
        case SlideType.PIN_DICT:
            return await process_dict(event, slide.text)
        case SlideType.QUIZ_OPTIONS:
            return await process_quiz_options(event, state, user_input, slide, session, db_session)
        case SlideType.QUIZ_INPUT_WORD:
            return await process_quiz_input_word(event, state, user_input, slide, session, db_session)
        case SlideType.QUIZ_INPUT_PHRASE:
            return await process_quiz_input_phrase(event, state, user_input, slide, session, db_session)
        case _:
            msg = f"Unexpected slide type: {slide.slide_type}"
            raise AssertionError(msg)


@asynccontextmanager
async def paranoid(state: FSMContext):
    data = await state.get_data()
    if 'slide_in_progress' in data:
        assert data['slide_in_progress'] is False
    await state.update_data(slide_in_progress=True)
    try:
        yield
    finally:
        await state.update_data(slide_in_progress=False)


async def show_slides(
    event: types.Message,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
    user_input: UserQuizInput | None = None,
) -> None:
    while session.has_next():
        async with paranoid(state):
            current_slide_id = session.get_slide()
            current_slide = await get_slide_by_id(current_slide_id, db_session)
            logger.info(f"Processing step={session.current_step}, slide_id={current_slide_id}")
            need_next = await process_slide(event, state, current_slide, session, db_session, user_input)
            user_input = None
            if not need_next:
                logger.info("returning...")
                return

            logger.info("continuing...")
            session.current_step += 1
            await db_session.flush()

    if session.in_extra:
        logger.info("finalizing extra...")
        await finalizing_extra(event, state, session, db_session)
        return

    logger.info("finalizing...")
    await finalizing(event, state, session, db_session)
