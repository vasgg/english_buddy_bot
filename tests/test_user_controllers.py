import logging
from unittest import IsolatedAsyncioTestCase

from sqlalchemy import select

from core.controllers.user_controllers import update_user_progress
from core.database.db import DatabaseConnector
from core.database.models import Base, User, UserProgress


class Test(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f'sqlite+aiosqlite://', echo=True)

        async with self.test_database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()

    async def creating_user(self):
        async with self.test_database.session_factory.begin() as session:
            new_user = User(
                telegram_id=234234234,
                first_name='vas',
                last_name='g',
                username='vasg',
            )
            session.add(new_user)
            await session.commit()
        return new_user

    async def check_user_progress(self, new_current_slide, new_user):
        async with self.test_database.session_factory.begin() as session:
            user_progress = select(UserProgress).where(UserProgress.user_id == new_user.id)
            result = await session.execute(user_progress)
            user_progress = result.scalar()
            logging.info(user_progress)
            self.assertEqual(user_progress.current_slide, new_current_slide)

    async def test_get_user_progress(self):
        new_user = await self.creating_user()

        current_slide = 50
        new_current_slide = 555

        async with self.test_database.session_factory.begin() as session:
            await update_user_progress(user_id=new_user.id, lesson_number=1, current_slide=current_slide, session=session)

        await self.check_user_progress(current_slide, new_user)

        async with self.test_database.session_factory.begin() as session:
            await update_user_progress(user_id=new_user.id, lesson_number=1, current_slide=new_current_slide, session=session)

        await self.check_user_progress(new_current_slide, new_user)
