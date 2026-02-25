from dataclasses import dataclass
from html import escape
import mimetypes
from pathlib import Path
import re

from aiogram import F, Router, types
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database.crud.media_asset import upsert_media_asset, update_media_comment_by_file_id
from enums import TelegramMediaType

router = Router()
settings = get_settings()

_FILE_ID_LINE_RE = re.compile(r"^file_id:\s*(?P<file_id>\S+)\s*$", re.IGNORECASE)
_MIME_EXTENSION_OVERRIDES = {
    "audio/ogg": "ogg",
    "image/gif": "gif",
    "video/mp4": "mp4",
}


@dataclass(frozen=True)
class MediaPayload:
    media_type: TelegramMediaType
    file_id: str
    file_unique_id: str
    file_name: str | None
    mime_type: str | None


def _extract_media_payload(message: types.Message) -> MediaPayload | None:
    if message.video:
        media = message.video
        return MediaPayload(
            media_type=TelegramMediaType.VIDEO,
            file_id=media.file_id,
            file_unique_id=media.file_unique_id,
            file_name=media.file_name,
            mime_type=media.mime_type,
        )
    if message.audio:
        media = message.audio
        return MediaPayload(
            media_type=TelegramMediaType.AUDIO,
            file_id=media.file_id,
            file_unique_id=media.file_unique_id,
            file_name=media.file_name,
            mime_type=media.mime_type,
        )
    if message.voice:
        media = message.voice
        return MediaPayload(
            media_type=TelegramMediaType.VOICE,
            file_id=media.file_id,
            file_unique_id=media.file_unique_id,
            file_name=None,
            mime_type=media.mime_type,
        )
    if message.animation:
        media = message.animation
        return MediaPayload(
            media_type=TelegramMediaType.ANIMATION,
            file_id=media.file_id,
            file_unique_id=media.file_unique_id,
            file_name=media.file_name,
            mime_type=media.mime_type,
        )
    if message.document:
        media = message.document
        return MediaPayload(
            media_type=TelegramMediaType.DOCUMENT,
            file_id=media.file_id,
            file_unique_id=media.file_unique_id,
            file_name=media.file_name,
            mime_type=media.mime_type,
        )
    return None


def _extract_extension(file_name: str | None, mime_type: str | None) -> str:
    if file_name:
        suffix = Path(file_name).suffix.removeprefix(".")
        if suffix:
            return suffix.lower()

    if mime_type:
        normalized = mime_type.lower()
        if normalized in _MIME_EXTENSION_OVERRIDES:
            return _MIME_EXTENSION_OVERRIDES[normalized]
        guessed = mimetypes.guess_extension(normalized)
        if guessed:
            return guessed.removeprefix(".").lower()

    return "unknown"


def _fallback_file_name(media_type: TelegramMediaType, file_unique_id: str, extension: str) -> str:
    if extension == "unknown":
        return f"{media_type.value}_{file_unique_id}"
    return f"{media_type.value}_{file_unique_id}.{extension}"


def _extract_file_id_from_bot_message_text(text: str | None) -> str | None:
    if not text:
        return None
    for line in text.splitlines():
        matched = _FILE_ID_LINE_RE.match(line.strip())
        if matched:
            return matched.group("file_id")
    return None


def _extract_file_id_from_replied_message(reply_to_message: types.Message) -> str | None:
    media_payload = _extract_media_payload(reply_to_message)
    if media_payload:
        return media_payload.file_id
    return _extract_file_id_from_bot_message_text(reply_to_message.text)


def _extract_caption_as_comment(message: types.Message) -> str | None:
    if message.caption is None:
        return None
    comment = message.caption.strip()
    return comment or None


def _build_media_info_message(
    *,
    file_name: str,
    extension: str,
    media_type: TelegramMediaType,
    file_id: str,
    comment: str | None,
) -> str:
    comment_text = escape(comment) if comment else "—"
    return (
        f"Имя файла: <b>{escape(file_name)}</b>\n"
        f"Расширение файла: <b>{escape(extension)}</b>\n"
        f"Тип медиа: <b>{escape(media_type.value)}</b>\n"
        f"file_id: <code>{escape(file_id)}</code>\n"
        f"Комментарий: {comment_text}"
    )


@router.message(F.chat.id == settings.MEDIA_CHAT_ID, F.video)
@router.message(F.chat.id == settings.MEDIA_CHAT_ID, F.audio)
@router.message(F.chat.id == settings.MEDIA_CHAT_ID, F.voice)
@router.message(F.chat.id == settings.MEDIA_CHAT_ID, F.animation)
@router.message(F.chat.id == settings.MEDIA_CHAT_ID, F.document)
async def media_info_handler(message: types.Message, db_session: AsyncSession) -> None:
    payload = _extract_media_payload(message)
    if payload is None:
        return

    extension = _extract_extension(file_name=payload.file_name, mime_type=payload.mime_type)
    file_name = payload.file_name or _fallback_file_name(payload.media_type, payload.file_unique_id, extension)
    comment = _extract_caption_as_comment(message)

    media_asset = await upsert_media_asset(
        file_id=payload.file_id,
        media_type=payload.media_type.value,
        file_name=file_name,
        file_extension=extension,
        mime_type=payload.mime_type,
        file_unique_id=payload.file_unique_id,
        comment=comment,
        db_session=db_session,
    )

    await message.answer(
        text=_build_media_info_message(
            file_name=file_name,
            extension=extension,
            media_type=payload.media_type,
            file_id=payload.file_id,
            comment=media_asset.comment,
        )
    )


@router.message(F.chat.id == settings.MEDIA_CHAT_ID, F.reply_to_message)
async def media_comment_reply_handler(message: types.Message, db_session: AsyncSession) -> None:
    if _extract_media_payload(message) is not None:
        return

    replied_message = message.reply_to_message
    if replied_message is None:
        return

    target_file_id = _extract_file_id_from_replied_message(replied_message)
    if target_file_id is None:
        await message.answer(
            "Чтобы добавить комментарий, отправьте reply текстом на сообщение с медиа "
            "или на сообщение бота, где есть строка file_id."
        )
        return

    if not message.text or not message.text.strip():
        await message.answer("В комментарий к медиа можно отправить только текст.")
        return

    updated_asset = await update_media_comment_by_file_id(
        file_id=target_file_id,
        comment=message.text.strip(),
        db_session=db_session,
    )
    if updated_asset is None:
        await message.answer(
            "Медиа с таким file_id не найдено в базе. "
            "Сначала отправьте файл в этот чат, чтобы бот его зарегистрировал."
        )
        return

    await message.answer(
        f"Комментарий обновлен.\nfile_id: <code>{escape(updated_asset.file_id)}</code>\n"
        f"Тип медиа: <b>{escape(updated_asset.media_type)}</b>"
    )
