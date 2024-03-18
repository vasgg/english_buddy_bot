from datetime import datetime
from unittest import IsolatedAsyncioTestCase

from database.database_connector import DatabaseConnector
from database.models.base import Base
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User

from database.crud.session import get_lesson_progress
from enums import SlideType, SessionStatus, SessionStartsFrom


class Test(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f"sqlite+aiosqlite://", echo=False)

        async with self.test_database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()

    async def test_session_in_progress(self):
        target_slide_id = 1050
        path = f"1.{target_slide_id}"

        async with self.test_database.session_factory.begin() as session:
            session.add(Lesson(title="abacaba", path=path))
            session.add(User(telegram_id=100500, first_name="Vasya", last_reminded_at=datetime.utcnow()))
            session.add(Slide(lesson_id=1, slide_type=SlideType.TEXT, id=target_slide_id))

        async with self.test_database.session_factory.begin() as session:
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

        async with self.test_database.session_factory() as session:
            session_slide_id = await get_lesson_progress(1, 1, session)
        self.assertEqual(target_slide_id, session_slide_id)
