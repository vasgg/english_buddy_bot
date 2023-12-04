import random
from unittest import IsolatedAsyncioTestCase

from sqlalchemy import update

from core.controllers.lesson_controllers import get_lesson
from core.controllers.slide_controllers import get_slide_by_id
from core.database.db import DatabaseConnector
from core.database.models import Base, Lesson, Slide
from core.resources.enums import SlideType


# class Test(IsolatedAsyncioTestCase):
#     async def asyncSetUp(self):
#         self.test_database = DatabaseConnector(url=f'sqlite+aiosqlite://', echo=True)
#
#         async with self.test_database.engine.begin() as conn:
#             await conn.run_sync(Base.metadata.create_all, checkfirst=True)
#
#         async with self.test_database.session_factory.begin() as session:
#             self.slide_ids = []
#             new_lesson = Lesson(title='test_lesson', slides_amount=10, exam_slide=5)
#             slides_amount = new_lesson.slides_amount
#             session.add(new_lesson)
#             for i in range(1, slides_amount + 1):
#                 slide_id = random.randint(1, 1000000000)
#                 new_slide = Slide(text=i * 3, slide_type=SlideType.TEXT, lesson_id=1)
#                 self.slide_ids.append(slide_id)
#                 session.add(new_slide)
#                 await session.flush()
#             await session.flush()
#
#             lesson_number = new_lesson.id
#             lesson = await get_lesson(lesson_number, session=session)
#             slides_amount = lesson.slides_amount
#             for i in range(1, slides_amount + 1):
#                 order_record = SlideOrder(lesson_id=lesson_number, slide_id=i, slide_index=i)
#                 session.add(order_record)
#             await session.commit()
#
#     async def asyncTearDown(self):
#         await self.test_database.engine.dispose()
#
#     async def test_get_slide_by_slide_order(self):
#         async with self.test_database.session_factory.begin() as session:
#             slide = await get_slide_by_id(lesson_id=1, slide_index=1, session=session)
#             self.assertEqual(slide.id, 1)
#             random_id = random.randint(1, 1000000000)
#             new_slide = Slide(id=random_id, text=3, slide_type=SlideType.TEXT, lesson_id=1)
#             session.add(new_slide)
#             await session.flush()
#
#             new_slide_index = update(SlideOrder).values(slide_id=random_id).filter(SlideOrder.slide_index == 1, SlideOrder.lesson_id == 1)
#             await session.execute(new_slide_index)
#             await session.commit()
#
#         async with self.test_database.session_factory.begin() as session:
#
#             slide = await get_slide_by_id(lesson_id=1, slide_index=1, session=session)
#             new_slide_index_by_order = slide.id
#             self.assertEqual(new_slide_index_by_order, random_id)
