from unittest import IsolatedAsyncioTestCase

from core.controllers.slide_controllers import get_slide_text
from core.database.db import db


class Test(IsolatedAsyncioTestCase):
    async def test_get_slide_text(self):
        async with db.session_factory.begin() as session:
            text = await get_slide_text(lesson_number=1, slide_number=1, session=session)
        print(text)
        # self.fail()
        await db.engine.dispose()
