from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.enums import EventType
from database.models.session import Session
from database.models.session_log import SessionLog


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
