import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from bot.controllers.slide_controllers import paranoid


async def get_flag(ctx: FSMContext):
    data = await ctx.get_data()
    return data['slide_in_progress']


@pytest.fixture()
def ctx():
    storage = MemoryStorage()
    ctx = FSMContext(storage, StorageKey(bot_id=0, chat_id=1, user_id=2))
    yield ctx


async def test_paranoid_happy_path(ctx):
    async with paranoid(ctx):
        assert (await get_flag(ctx)) is True
    assert (await get_flag(ctx)) is False


async def test_paranoid_exc(ctx):
    try:
        async with paranoid(ctx):
            assert (await get_flag(ctx)) is True
            raise ValueError("123")
    except ValueError:
        pass
    assert (await get_flag(ctx)) is False


async def test_paranoid_assertion(ctx):
    async with paranoid(ctx):
        with pytest.raises(AssertionError):
            async with paranoid(ctx):
                pass
