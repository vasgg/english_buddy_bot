import logging

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
from database.models.session import Session
from database.models.slide import Slide
from enums import SlideType
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.Logger(__name__)


async def get_steps_to_current_slide(first_slide_id: int, target_slide_id: int, path: str) -> int:
    slide_ids_str = path.split(".")
    slide_ids = [int(id_str) for id_str in slide_ids_str]
    start_index = slide_ids.index(first_slide_id)
    target_index = slide_ids.index(target_slide_id)
    steps = abs(target_index - start_index)
    return steps


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


async def show_slides(
    event: types.Message,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
    user_input: UserQuizInput | None = None,
) -> None:
    while session.has_next():
        current_slide = session.get_slide()
        logger.info(f"Processing step={session.current_step}, slide_id={current_slide}")
        need_next = await process_slide(event, state, current_slide, session, db_session, user_input)
        if not need_next:
            logger.info("breaking...")
            break

        logger.info("continuing...")

        session.current_step += 1
        await db_session.flush()

    if session.in_extra:
        logger.info("finalizing extra...")
        await finalizing_extra()
        return

    logger.info("finalizing...")
    await finalizing(event, state, session, db_session)
