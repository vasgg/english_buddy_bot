import logging

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.session import update_session
from database.crud.slide import get_slide_by_id
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User

logger = logging.Logger(__name__)


async def session_routine(
    bot: Bot,
    user: User,
    slide_id: int,
    current_step: int,
    state: FSMContext,
    session: Session,
    db_session: AsyncSession,
) -> None:
    from bot.controllers.slide_controllers import last_slide_processing, slides_routine

    slide: Slide = await get_slide_by_id(slide_id=slide_id, db_session=db_session)
    path = [int(elem) for elem in session.path.split(".")]
    if not slide:
        logger.error(f'Slide {slide_id} not found')
        return
    await update_session(
        user_id=user.id,
        lesson_id=session.lesson_id,
        current_slide_id=slide.id,
        current_step=current_step,
        session_id=session.id,
        db_session=db_session,
    )
    if current_step != len(path) + 1:
        await slides_routine(
            slide=slide,
            bot=bot,
            user=user,
            path=path,
            current_step=current_step,
            state=state,
            session=session,
            db_session=db_session,
        )
    else:
        await last_slide_processing(
            bot=bot,
            path=path,
            user=user,
            state=state,
            session=session,
            db_session=db_session,
        )


async def find_first_exam_slide(slide_ids, db_session: AsyncSession) -> int | None:
    for slide_id in slide_ids[1:]:
        slide: Slide = await get_slide_by_id(slide_id, db_session)
        if slide.is_exam_slide:
            return slide_id
    return None
