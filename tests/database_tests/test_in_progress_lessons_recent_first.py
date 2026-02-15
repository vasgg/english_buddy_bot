from datetime import datetime, timezone

from database.crud.session import get_in_progress_lessons_recent_first
from database.database_connector import DatabaseConnector
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.slide import Slide
from database.models.user import User
from enums import SessionStartsFrom, SessionStatus, SlideType


async def test_get_in_progress_lessons_recent_first_returns_latest_session_per_lesson(db: 'DatabaseConnector'):
    async with db.session_factory.begin() as session:
        session.add(User(telegram_id=100500, fullname='Vasya', last_reminded_at=datetime.now(timezone.utc)))
        session.add(Lesson(title='Lesson 1', path='11.12.13'))
        session.add(Lesson(title='Lesson 2', path='21.22'))

        session.add_all(
            [
                Slide(id=11, lesson_id=1, slide_type=SlideType.TEXT),
                Slide(id=12, lesson_id=1, slide_type=SlideType.TEXT),
                Slide(id=13, lesson_id=1, slide_type=SlideType.TEXT),
                Slide(id=21, lesson_id=2, slide_type=SlideType.TEXT),
                Slide(id=22, lesson_id=2, slide_type=SlideType.TEXT),
            ]
        )

    old = datetime(2024, 1, 1, 10, 0, 0)
    newer = datetime(2024, 1, 2, 10, 0, 0)
    newest = datetime(2024, 1, 3, 10, 0, 0)

    async with db.session_factory.begin() as session:
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.IN_PROGRESS,
                starts_from=SessionStartsFrom.BEGIN,
                current_step=0,
                path='11.12.13',
                created_at=old,
            ),
        )
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.IN_PROGRESS,
                starts_from=SessionStartsFrom.BEGIN,
                current_step=1,
                path='11.12.13',
                created_at=newer,
            ),
        )
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.ABORTED,
                starts_from=SessionStartsFrom.BEGIN,
                path='11.12.13',
                created_at=newest,
            ),
        )
        session.add(
            Session(
                lesson_id=2,
                user_id=1,
                status=SessionStatus.IN_PROGRESS,
                starts_from=SessionStartsFrom.BEGIN,
                current_step=0,
                path='21.22',
                created_at=newest,
            ),
        )

    async with db.session_factory() as session:
        in_progress = await get_in_progress_lessons_recent_first(user_id=1, db_session=session)

    assert [s.lesson_id for s in in_progress] == [2, 1]
    assert [s.created_at for s in in_progress] == [newest, newer]


async def test_get_in_progress_lessons_recent_first_prefers_higher_id_on_same_timestamp(db: 'DatabaseConnector'):
    async with db.session_factory.begin() as session:
        session.add(User(telegram_id=100500, fullname='Vasya', last_reminded_at=datetime.now(timezone.utc)))
        session.add(Lesson(title='Lesson 1', path='11.12'))
        session.add_all(
            [
                Slide(id=11, lesson_id=1, slide_type=SlideType.TEXT),
                Slide(id=12, lesson_id=1, slide_type=SlideType.TEXT),
            ]
        )

    same_time = datetime(2024, 1, 1, 10, 0, 0)

    async with db.session_factory.begin() as session:
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.IN_PROGRESS,
                starts_from=SessionStartsFrom.BEGIN,
                current_step=0,
                path='11.12',
                created_at=same_time,
            ),
        )
        session.add(
            Session(
                lesson_id=1,
                user_id=1,
                status=SessionStatus.IN_PROGRESS,
                starts_from=SessionStartsFrom.BEGIN,
                current_step=1,
                path='11.12',
                created_at=same_time,
            ),
        )

    async with db.session_factory() as session:
        in_progress = await get_in_progress_lessons_recent_first(user_id=1, db_session=session)

    assert len(in_progress) == 1
    assert in_progress[0].current_step == 1
