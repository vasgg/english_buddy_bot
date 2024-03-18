from unittest import IsolatedAsyncioTestCase

from fastapi.testclient import TestClient

from config import get_settings, Settings
from database.database_connector import DatabaseConnector
from database.models.base import Base
from webapp.create_app import create_app
from webapp.db import get_db


def override_settings():
    return Settings(
        allowed_image_formats=[],
    )


class TestAllHandlesRespond(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f"sqlite+aiosqlite://", echo=False)

        async with self.test_database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

        app = create_app()

        app.dependency_overrides[get_settings] = override_settings
        app.dependency_overrides[get_db] = lambda: self.test_database

        self.client = TestClient(app)

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()

    async def test_get(self):
        xs = ['/api/lessons', '/api/texts', '/api/reactions', '/api/newsletter']
        for url in xs:
            resp = self.client.get(url)
            resp.raise_for_status()
