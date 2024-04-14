from datetime import datetime, timezone

from database.crud.session import get_current_session
from database.database_connector import DatabaseConnector
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User
from enums import SessionStartsFrom, SessionStatus, SlideType


async def test_session_in_progress(db: 'DatabaseConnector'):
    slide_id = 1050
    path = f"1.{slide_id}"
    target_step = 199

    async with db.session_factory.begin() as session:
        session.add(Lesson(title="abacaba", path=path))
        session.add(User(telegram_id=100500, fullname="Vasya", last_reminded_at=datetime.now(timezone.utc)))
        session.add(Slide(lesson_id=1, slide_type=SlideType.TEXT, id=slide_id))

    async with db.session_factory.begin() as session:
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.IN_PROGRESS,
                starts_from=SessionStartsFrom.BEGIN,
                current_step=target_step,
                path=path,
            ),
        )
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.ABORTED,
                starts_from=SessionStartsFrom.BEGIN,
                path=path,
            ),
        )
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.COMPLETED,
                starts_from=SessionStartsFrom.BEGIN,
                path=path,
            ),
        )

    async with db.session_factory() as session:
        current_session = await get_current_session(1, 1, session)

    assert target_step == current_session.current_step
