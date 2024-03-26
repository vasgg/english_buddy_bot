from aiogram import Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.lesson_controllers import logger
from database.crud.session import update_session
from database.crud.slide import get_slide_by_id
from database.models.session import Session
from database.models.session_log import SessionLog
from database.models.slide import Slide
from database.models.user import User
from enums import EventType


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
    path = session.get_path()
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
    if current_step != len(path) + 2:
        await slides_routine(
            slide=slide,
            bot=bot,
            user=user,
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


async def log_quiz_answer(
    session: Session, is_correct: bool | None, mode: EventType, event, slide, db_session: AsyncSession
):
    match mode:
        case EventType.MESSAGE:
            data = event.text
        case EventType.CALLBACK_QUERY:
            if ':' in event.data:
                data = event.data.split(':')[-1]
            else:
                data = event.data
        case EventType.HINT:
            data = 'show_hint'
        case EventType.CONTINUE:
            data = 'continue'
        case _:
            assert False, f'Unknown event type: {mode}'
    json_event = event.model_dump_json(exclude_unset=True)
    session_log = SessionLog(
        session_id=session.id,
        slide_id=session.current_slide_id,
        slide_type=slide.slide_type,
        data=data,
        is_correct=is_correct,
        update=json_event,
    )
    db_session.add(session_log)
