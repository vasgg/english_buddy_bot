import pytest
from database.tables_helper import populate_db
from httpx import AsyncClient


@pytest.mark.parametrize(
    "url",
    [
        "/api/lessons",
        "/api/reactions",
        "/api/newsletter",
    ],
)
async def test_get(client: AsyncClient, db, url):
    await populate_db(db)
    resp = await client.get(url)
    assert resp.status_code == 200
