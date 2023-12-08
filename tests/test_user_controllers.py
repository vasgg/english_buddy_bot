from unittest import IsolatedAsyncioTestCase

from core.controllers.session_controller import get_lesson_progress
from core.database.database_connector import DatabaseConnector
from core.database.models import Base, Session, Lesson, User, Slide
from core.resources.enums import SlideType, SessionStatus


class Test(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f'sqlite+aiosqlite://', echo=True)

        async with self.test_database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()

    async def test_session_in_progress(self):
        target_slide_id = 1050
        async with self.test_database.session_factory.begin() as session:
            session.add(Lesson(title="abacaba"))
            session.add(User(telegram_id=100500, first_name="Vasya"))
            session.add(Slide(lesson_id=1, slide_type=SlideType.TEXT, id=target_slide_id))

        async with self.test_database.session_factory.begin() as session:
            session.add(Session(lesson_id=1, user_id=1, current_slide_id=target_slide_id, status=SessionStatus.IN_PROGRESS))
            session.add(Session(lesson_id=1, user_id=1, current_slide_id=target_slide_id, status=SessionStatus.ABORTED))
            session.add(Session(lesson_id=1, user_id=1, current_slide_id=target_slide_id, status=SessionStatus.COMPLETED))

        async with self.test_database.session_factory() as session:
            session_slide_id = await get_lesson_progress(1, 1, session)
        self.assertEqual(target_slide_id, session_slide_id)

#
#     async def creating_user(self):
#         async with self.test_database.session_factory.begin() as session:
#             new_user = User(
#                 telegram_id=234234234,
#                 first_name='vas',
#                 last_name='g',
#                 username='vasg',
#             )
#             session.add(new_user)
#             await session.commit()
#         return new_user
#
#     async def check_user_progress(self, new_current_slide, new_user):
#         async with self.test_database.session_factory.begin() as session:
#             user_progress = select(UserProgress).where(UserProgress.user_id == new_user.id)
#             result = await session.execute(user_progress)
#             user_progress = result.scalar()
#             logging.info(user_progress)
#             self.assertEqual(user_progress.current_slide, new_current_slide)
#
#     async def test_get_user_progress(self):
#         new_user = await self.creating_user()
#
#         current_slide = 50
#         new_current_slide = 555
#
#         async with self.test_database.session_factory.begin() as session:
#             await update_user_progress(user_id=new_user.id, lesson_number=1, current_slide=current_slide, session=session)
#
#         await self.check_user_progress(current_slide, new_user)
#
#         async with self.test_database.session_factory.begin() as session:
#             await update_user_progress(user_id=new_user.id, lesson_number=1, current_slide=new_current_slide, session=session)
#
#         await self.check_user_progress(new_current_slide, new_user)
