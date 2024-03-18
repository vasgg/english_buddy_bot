import random
from dataclasses import dataclass
from datetime import datetime
from unittest import IsolatedAsyncioTestCase

from database.crud.user import (
    add_user_to_db,
    get_user_from_db,
    toggle_user_paywall_access,
    set_user_reminders,
    get_all_users_with_reminders,
    update_last_reminded_at,
)
from database.database_connector import DatabaseConnector
from database.models.base import Base
from database.models.user import User


# TODO: разобраться как обходить констраинты


def rand_bool() -> bool:
    return random.random() < 0.5


@dataclass
class User:
    id: int
    first_name: str
    last_name: str
    username: str


class TestUserCrud(IsolatedAsyncioTestCase):
    u = User(id=123, first_name="aba", last_name="caba", username="@capybara")

    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f"sqlite+aiosqlite://", echo=False)

        async with self.test_database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()

    async def createTestUser(self):
        async with self.test_database.session_factory.begin() as session:
            return await add_user_to_db(self.u, session)

    async def test_user_cr_single_session(self):
        async with self.test_database.session_factory.begin() as session:
            db_user = await add_user_to_db(self.u, session)
            selected_user = await get_user_from_db(self.u.id, session)

        self.assertEqual(db_user, selected_user)

    async def test_user_cr_separate_sessions(self):
        db_user = await self.createTestUser()

        async with self.test_database.session_factory.begin() as session:
            selected_user = await get_user_from_db(self.u.id, session)

        self.assertEqual(db_user.id, selected_user.id)

    async def test_toggle_user_paywall_access(self):
        db_user = await self.createTestUser()

        async with self.test_database.session_factory.begin() as session:
            await toggle_user_paywall_access(db_user.id, session)
            selected_user = await get_user_from_db(self.u.id, session)

        self.assertNotEqual(db_user.paywall_access, selected_user.paywall_access)

    async def test_set_user_reminders(self):
        new_reminder_freq = random.randint(1, 1000)
        db_user = await self.createTestUser()

        self.assertIsNone(db_user.reminder_freq)

        async with self.test_database.session_factory.begin() as session:
            await set_user_reminders(db_user.id, new_reminder_freq, session)

        async with self.test_database.session_factory.begin() as session:
            selected_user = await get_user_from_db(self.u.id, session)

        self.assertEqual(selected_user.reminder_freq, new_reminder_freq)

    async def test_get_all_users_with_reminders(self):
        expected_users_with_reminders = set()
        async with self.test_database.session_factory.begin() as session:
            for i in range(1, 100):
                user = await add_user_to_db(
                    User(id=i, first_name="aba", last_name="caba", username="@capybara"), session
                )
                if rand_bool():
                    expected_users_with_reminders.add(user.id)
                    await set_user_reminders(user.id, 1, session)

        async with self.test_database.session_factory.begin() as session:
            actual_list = set(u.id for u in await get_all_users_with_reminders(session))

        self.assertSetEqual(expected_users_with_reminders, actual_list)

    async def test_update_last_reminded_at(self):
        db_user = await self.createTestUser()
        dt = datetime.utcnow()
        self.assertNotEqual(db_user.last_reminded_at, dt)
        async with self.test_database.session_factory.begin() as session:
            await update_last_reminded_at(db_user.id, dt, session)
            selected_user = await get_user_from_db(self.u.id, session)

        self.assertEqual(selected_user.last_reminded_at, dt)
