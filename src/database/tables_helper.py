from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncEngine

from config import get_settings
from database.database_connector import DatabaseConnector
from database.models.base import Base
# noinspection PyUnresolvedReferences
from database.models.lesson import Lesson
# noinspection PyUnresolvedReferences
import database.models.quiz_answer_log
# noinspection PyUnresolvedReferences
from database.models.reaction import Reaction, ReactionType
# noinspection PyUnresolvedReferences
import database.models.session
# noinspection PyUnresolvedReferences
from database.models.slide import Slide, SlideType
# noinspection PyUnresolvedReferences
import database.models.sticker
# noinspection PyUnresolvedReferences
import database.models.text
# noinspection PyUnresolvedReferences
from database.models.user import User


async def create_or_drop_db(engine: AsyncEngine, create: bool = True):
    async with engine.begin() as conn:
        if create:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        else:
            await conn.run_sync(Base.metadata.drop_all)


async def populate_db(dc: DatabaseConnector):
    target_slide_id = 1050

    async with dc.session_factory.begin() as session:
        session.add(Lesson(title="abacaba", path=f"{target_slide_id}", index=1))
        session.add(User(telegram_id=100500, first_name="Vasya", last_reminded_at=datetime.now(timezone.utc)))
        session.add(Slide(lesson_id=1, slide_type=SlideType.TEXT, id=target_slide_id))
        session.add(Reaction(type=ReactionType.WRONG, text="wrong"))
        session.add(Reaction(type=ReactionType.RIGHT, text="right"))
        await session.commit()


def get_db() -> DatabaseConnector:
    settings = get_settings()
    return DatabaseConnector(url=settings.aiosqlite_db_url, echo=settings.db_echo)


if __name__ == '__main__':
    import asyncio

    db = get_db()
    asyncio.run(create_or_drop_db(db.engine))
