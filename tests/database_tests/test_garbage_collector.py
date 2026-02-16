from database.database_connector import DatabaseConnector
from database.garbage_helper import collect_garbage
from database.models.lesson import Lesson
from database.models.slide import Slide
from enums import LessonStatus, SlideType


async def test_garbage_collector(db: "DatabaseConnector"):
    slide_id = 1
    path = f"1.{slide_id}"

    async with db.session_factory.begin() as session:
        session.add(Lesson(title="abacaba", path=path, is_active=LessonStatus.DISABLED))
        session.add(Slide(lesson_id=1, slide_type=SlideType.TEXT, id=slide_id))

    async with db.session_factory.begin() as session:
        await collect_garbage(session)
