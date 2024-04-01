from aiogram import types
from database.crud.answer import get_random_sticker_id
from enums import SlideType, StickerType
from sqlalchemy.ext.asyncio import AsyncSession


async def process_sticker(
    event: types.Message,
    slide_type: SlideType,
    db_session: AsyncSession,
) -> bool:
    sticker_type = StickerType.SMALL if slide_type == SlideType.SMALL_STICKER else StickerType.BIG
    await event.answer_sticker(sticker=await get_random_sticker_id(mode=sticker_type, db_session=db_session))
    return True
