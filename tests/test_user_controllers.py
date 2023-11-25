from unittest import IsolatedAsyncioTestCase

from core.controllers.user_controllers import check_user_progress
from core.database.db import db


class Test(IsolatedAsyncioTestCase):
    async def test_check_user_progress(self):
        async with db.session_factory.begin() as session:
            progress = await check_user_progress(user_id=1, lesson_number=1, session=session)
        print(progress)
        # self.fail()
        await db.engine.dispose()
