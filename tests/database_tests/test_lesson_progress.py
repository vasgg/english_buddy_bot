from datetime import datetime

from database.crud.session import get_lesson_progress
from database.database_connector import DatabaseConnector
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User
from enums import SlideType, SessionStatus, SessionStartsFrom


async def test_session_in_progress(db: 'DatabaseConnector'):
    target_slide_id = 1050
    path = f"1.{target_slide_id}"

    async with db.session_factory.begin() as session:
        session.add(Lesson(title="abacaba", path=path))
        session.add(User(telegram_id=100500, first_name="Vasya", last_reminded_at=datetime.utcnow()))
        session.add(Slide(lesson_id=1, slide_type=SlideType.TEXT, id=target_slide_id))

    async with db.session_factory.begin() as session:
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                current_slide_id=target_slide_id,
                status=SessionStatus.IN_PROGRESS,
                starts_from=SessionStartsFrom.BEGIN,
                path=path,
            )
        )
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                current_slide_id=target_slide_id,
                status=SessionStatus.ABORTED,
                starts_from=SessionStartsFrom.BEGIN,
                path=path,
            )
        )
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                current_slide_id=target_slide_id,
                status=SessionStatus.COMPLETED,
                starts_from=SessionStartsFrom.BEGIN,
                path=path,
            )
        )

    async with db.session_factory() as session:
        session_slide_id = await get_lesson_progress(1, 1, session)

    assert target_slide_id == session_slide_id
