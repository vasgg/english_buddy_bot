import random
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from database.crud.user import (
    add_user_to_db,
    get_all_users_with_reminders,
    get_user_from_db,
    set_user_reminders,
    toggle_user_paywall_access,
    update_last_reminded_at,
)
from database.models.user import User as UserDbModel

# TODO: разобраться как обходить констраинты


def rand_bool() -> bool:
    return random.random() < 0.5


@dataclass
class User:
    id: int
    first_name: str
    last_name: str
    username: str


@pytest.fixture()
async def user() -> User:
    return User(id=123, first_name="aba", last_name="caba", username="@capybara")


@pytest.fixture()
async def user_db_model(db, user: User) -> UserDbModel:
    async with db.session_factory.begin() as session:
        return await add_user_to_db(user, session)


async def test_user_cr_single_session(db, user: User):
    async with db.session_factory.begin() as session:
        db_user = await add_user_to_db(user, session)
        selected_user = await get_user_from_db(user.id, session)

    assert db_user == selected_user


async def test_user_cr_separate_sessions(user_db_model: UserDbModel, db, user: User):
    async with db.session_factory.begin() as session:
        selected_user = await get_user_from_db(user.id, session)

    assert user_db_model.id == selected_user.id


async def test_toggle_user_paywall_access(user_db_model: UserDbModel, db, user: User):
    async with db.session_factory.begin() as session:
        await toggle_user_paywall_access(user_db_model.id, session)
        selected_user = await get_user_from_db(user.id, session)

    assert user_db_model.paywall_access is not selected_user.paywall_access


async def test_set_user_reminders(user_db_model: UserDbModel, db, user: User):
    new_reminder_freq = random.randint(1, 1000)

    assert user_db_model.reminder_freq is None

    async with db.session_factory.begin() as session:
        await set_user_reminders(user_db_model.id, new_reminder_freq, session)

    async with db.session_factory.begin() as session:
        selected_user = await get_user_from_db(user.id, session)

    assert selected_user.reminder_freq == new_reminder_freq


async def test_get_all_users_with_reminders(db, user: User):
    expected_users_with_reminders = set()
    async with db.session_factory.begin() as session:
        for i in range(1, 100):
            user = await add_user_to_db(User(id=i, first_name="aba", last_name="caba", username="@capybara"), session)
            if rand_bool():
                expected_users_with_reminders.add(user.id)
                await set_user_reminders(user.id, 1, session)

    async with db.session_factory.begin() as session:
        actual = set(u.id for u in await get_all_users_with_reminders(session))

    assert expected_users_with_reminders == actual


async def test_update_last_reminded_at(user_db_model: UserDbModel, db, user: User):
    dt = datetime.now(timezone.utc)
    assert user_db_model.last_reminded_at != dt
    async with db.session_factory.begin() as session:
        await update_last_reminded_at(user_db_model.id, dt, session)
        selected_user = await get_user_from_db(user.id, session)

    assert selected_user.last_reminded_at == dt
