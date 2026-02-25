import asyncio

from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.keyboards import get_further_button
from database.crud.media_asset import get_media_asset_by_id
from database.models.session import Session
from database.models.slide import Slide
from enums import KeyboardType, TelegramMediaType


async def process_media(
    event: types.Message,
    slide: Slide,
    session: Session,
    db_session: AsyncSession,
) -> bool:
    markup = None
    if slide.delay:
        # noinspection PyTypeChecker
        await asyncio.sleep(slide.delay)
    if slide.keyboard_type == KeyboardType.FURTHER:
        markup = get_further_button()

    if slide.media_asset_id is None:
        await event.answer("⚠️ В слайде не указан media_asset_id.")
        return True

    media_asset = await get_media_asset_by_id(slide.media_asset_id, db_session)
    if media_asset is None:
        await event.answer("⚠️ Медиа не найдено в базе. Обновите слайд в админке.")
        return True

    match media_asset.media_type:
        case TelegramMediaType.VIDEO.value:
            await event.answer_video(video=media_asset.file_id, reply_markup=markup)
        case TelegramMediaType.AUDIO.value:
            await event.answer_audio(audio=media_asset.file_id, reply_markup=markup)
        case TelegramMediaType.VOICE.value:
            await event.answer_voice(voice=media_asset.file_id, reply_markup=markup)
        case TelegramMediaType.ANIMATION.value:
            await event.answer_animation(animation=media_asset.file_id, reply_markup=markup)
        case TelegramMediaType.DOCUMENT.value:
            await event.answer_document(document=media_asset.file_id, reply_markup=markup)
        case _:
            await event.answer(f"⚠️ Неподдерживаемый тип медиа: {media_asset.media_type}")
            return True

    return slide.keyboard_type != KeyboardType.FURTHER
