from unittest import IsolatedAsyncioTestCase

from core.controllers.session_controller import get_lesson_progress
from core.database.database_connector import DatabaseConnector
from core.database.models.base import Base
from core.database.models.lesson import Lesson
from core.database.models.session import Session
from core.database.models.slide import Slide
from core.database.models.user import User
from core.resources.enums import SlideType, SessionStatus


class Test(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f"sqlite+aiosqlite://", echo=True)

        async with self.test_database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()

    async def test_session_in_progress(self):
        target_slide_id = 1050
        async with self.test_database.session_factory.begin() as session:
            session.add(Lesson(title="abacaba"))
            session.add(User(telegram_id=100500, first_name="Vasya"))
            session.add(
                Slide(lesson_id=1, slide_type=SlideType.TEXT, id=target_slide_id)
            )

        async with self.test_database.session_factory.begin() as session:
            session.add(
                Session(
                    lesson_id=1,
                    user_id=1,
                    current_slide_id=target_slide_id,
                    status=SessionStatus.IN_PROGRESS,
                )
            )
            session.add(
                Session(
                    lesson_id=1,
                    user_id=1,
                    current_slide_id=target_slide_id,
                    status=SessionStatus.ABORTED,
                )
            )
            session.add(
                Session(
                    lesson_id=1,
                    user_id=1,
                    current_slide_id=target_slide_id,
                    status=SessionStatus.COMPLETED,
                )
            )

        async with self.test_database.session_factory() as session:
            session_slide_id = await get_lesson_progress(1, 1, session)
        self.assertEqual(target_slide_id, session_slide_id)
