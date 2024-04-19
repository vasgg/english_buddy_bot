from httpx import AsyncClient
import pytest

from database.tables_helper import populate_db


@pytest.mark.parametrize(
    "url",
    [
        "/api/",
        "/api/favicon.ico/",
        "/api/files/",
        "/api/forms/search/",
        "/api/lessons/",
        "/api/lessons/edit/",
        "/api/lessons/up_button/",
        "/api/lessons/down_button/",
        "/api/lessons/plus_button/",
        "/api/lessons/confirm_delete/",
        "/api/lessons/delete/",
        "/api/newsletter/",
        "/api/newsletter/sent/",
        "/api/newsletter/send/",
        "/api/lessons/new/",
        "/api/reactions/",
        "/api/reactions/add/",
        "/api/reactions/add/right/",
        "/api/reactions/add/wrong/",
        "/api/reactions/edit/",
        "/api/reactions/delete/",
        "/api/reactions/confirm_delete/",
        "/api/slides/",
        "/api/slides/plus_button/regular/",
        "/api/slides/plus_button/extra/",
        "/api/statistics/",
        "/api/texts/",
        "/api/texts/edit/",
        "/api/users/",
        "/api/users/edit/",
    ],
)
async def test_get(client: AsyncClient, db, url):
    await populate_db(db)
    resp = await client.get(url)
    assert resp.status_code == 200
