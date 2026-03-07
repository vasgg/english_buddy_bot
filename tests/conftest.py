from httpx import ASGITransport, AsyncClient
import os
import pytest

from config import Settings, get_settings
from database.database_connector import DatabaseConnector
from database.models.base import Base
from database.tables_helper import get_db
from enums import Stage
from webapp.create_app import create_app


def _get_test_database_url() -> str:
    db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "Set TEST_DATABASE_URL (or DATABASE_URL) for tests. Expected PostgreSQL DSN with asyncpg driver."
        )
    if not db_url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("Tests are PostgreSQL-only. Use TEST_DATABASE_URL in format postgresql+asyncpg://...")
    return db_url


@pytest.fixture()
async def db():
    test_database = DatabaseConnector(url=_get_test_database_url(), echo=True)

    async with test_database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True)
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    yield test_database

    async with test_database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True)
    await test_database.engine.dispose()


def override_settings():
    return Settings(
        BOT_TOKEN="test-token",
        ADMIN=1,
        SUB_ADMINS=[],
        TEACHERS=[],
        MEDIA_CHAT_ID=-1000000000000,
        DATABASE_URL=_get_test_database_url(),
        TOP_BAD_SLIDES_COUNT=10,
        STAGE=Stage.DEV,
        REDIS_URL="redis://localhost:6379/1",
        TASKIQ_REDIS_URL="redis://localhost:6379/2",
        allowed_image_formats=[],
    )


@pytest.fixture()
async def client(db):
    app = create_app()

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_db] = lambda: db

    # noinspection PyTypeChecker
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
