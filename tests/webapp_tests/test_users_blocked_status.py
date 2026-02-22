from datetime import datetime, timezone

from database.models.user import User
from pydantic import SecretStr
import webapp.routers.users as users_router


class FakeForbiddenError(Exception):
    pass


class FakeBotForbidden:
    def __init__(self, *args, **kwargs) -> None:
        del args, kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        del exc_type, exc, tb
        return False

    async def send_message(self, *, chat_id: int, text: str) -> None:
        del chat_id, text
        raise FakeForbiddenError("blocked")


class FakeBotOk:
    def __init__(self, *args, **kwargs) -> None:
        del args, kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        del exc_type, exc, tb
        return False

    async def send_message(self, *, chat_id: int, text: str) -> None:
        del chat_id, text


class FakeSettings:
    BOT_TOKEN = SecretStr("test-token")


def _patch_settings(monkeypatch) -> None:
    monkeypatch.setattr(users_router, "get_settings", lambda: FakeSettings())


async def test_users_page_shows_blocked_users_count(client, db):
    now = datetime.now(timezone.utc)
    async with db.session_factory.begin() as session:
        session.add_all(
            [
                User(telegram_id=101, fullname="blocked", last_reminded_at=now, bot_blocked=True),
                User(telegram_id=102, fullname="active", last_reminded_at=now, bot_blocked=False),
            ]
        )

    response = await client.get("/api/users", headers={"accept": "application/json"})

    assert response.status_code == 200
    assert "🚫 заблокировали бота: 1" in str(response.json())
    assert "bot_blocked_icon" in str(response.json())


async def test_send_message_marks_user_blocked_on_forbidden(client, db, monkeypatch):
    now = datetime.now(timezone.utc)
    async with db.session_factory.begin() as session:
        user = User(telegram_id=103, fullname="forbidden", last_reminded_at=now, bot_blocked=False)
        session.add(user)
        await session.flush()
        user_id = user.id

    monkeypatch.setattr(users_router, "TelegramForbiddenError", FakeForbiddenError)
    monkeypatch.setattr(users_router, "Bot", FakeBotForbidden)
    _patch_settings(monkeypatch)

    response = await client.post(
        f"/api/users/send_message/{user_id}/",
        data={"message": "hello"},
        headers={"accept": "application/json"},
    )

    assert response.status_code == 200
    assert "error=forbidden" in response.text

    async with db.session_factory() as session:
        updated_user = await session.get(User, user_id)

    assert updated_user is not None
    assert updated_user.bot_blocked is True


async def test_send_message_clears_blocked_flag_on_success(client, db, monkeypatch):
    now = datetime.now(timezone.utc)
    async with db.session_factory.begin() as session:
        user = User(telegram_id=104, fullname="restored", last_reminded_at=now, bot_blocked=True)
        session.add(user)
        await session.flush()
        user_id = user.id

    monkeypatch.setattr(users_router, "Bot", FakeBotOk)
    _patch_settings(monkeypatch)

    response = await client.post(
        f"/api/users/send_message/{user_id}/",
        data={"message": "hello"},
        headers={"accept": "application/json"},
    )

    assert response.status_code == 200
    assert "status=sent" in response.text

    async with db.session_factory() as session:
        updated_user = await session.get(User, user_id)

    assert updated_user is not None
    assert updated_user.bot_blocked is False
