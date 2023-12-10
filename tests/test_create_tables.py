import logging
from unittest import IsolatedAsyncioTestCase

from sqlalchemy import inspect

from core.database.database_connector import DatabaseConnector
from core.database.models.base import Base
from core.utils.create_tables import create_or_drop_db


class Test(IsolatedAsyncioTestCase):
    def setUp(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s: "
            "%(filename)s: "
            "%(levelname)s: "
            "%(funcName)s(): "
            "%(lineno)d:\t"
            "%(message)s",
        )

    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f"sqlite+aiosqlite://", echo=True)

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()

    async def test_session_in_progress(self):
        await create_or_drop_db(self.test_database.engine)
        target_dbs = {
            "users_completed_lessons",
            "answers",
            "lessons",
            "sessions",
            "session_logs",
            "slides",
            "users",
        }
        metadata_keys = Base.metadata.tables.keys()
        self.assertEqual(
            target_dbs,
            metadata_keys,
            f"Difference: {target_dbs - metadata_keys}, {metadata_keys - target_dbs}",
        )

        inspector = inspect(self.test_database.engine)
        inspector
