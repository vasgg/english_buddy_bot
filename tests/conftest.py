import pytest
from httpx import AsyncClient, ASGITransport

from config import get_settings, Settings
from database.database_connector import DatabaseConnector
from database.models.base import Base
from database.tables_helper import get_db
from webapp.create_app import create_app


@pytest.fixture
async def db():
    test_database = DatabaseConnector(url=f"sqlite+aiosqlite://", echo=False)

    async with test_database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    yield test_database

    await test_database.engine.dispose()


def override_settings():
    return Settings(
        allowed_image_formats=[],
    )


@pytest.fixture
async def client(db):
    app = create_app()

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_db] = lambda: db

    # noinspection PyTypeChecker
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
