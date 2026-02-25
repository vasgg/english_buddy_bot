import os

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN", "1")
os.environ.setdefault("SUB_ADMINS", "[]")
os.environ.setdefault("TEACHERS", "[]")
os.environ.setdefault("MEDIA_CHAT_ID", "-1000000000000")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@127.0.0.1:5432/db")
os.environ.setdefault("TOP_BAD_SLIDES_COUNT", "1")
os.environ.setdefault("STAGE", "dev")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("TASKIQ_REDIS_URL", "redis://localhost:6379/2")

from bot.handlers.media_info_handlers import _extract_extension, _extract_file_id_from_bot_message_text


def test_extract_extension_prefers_filename_suffix():
    assert _extract_extension("sample.mp4", "application/octet-stream") == "mp4"


def test_extract_extension_falls_back_to_mime_type():
    assert _extract_extension(None, "audio/ogg") == "ogg"


def test_extract_file_id_from_bot_message_text():
    text = "Имя файла: x\nfile_id: BAADAgADbXXXXXXXXXXX\nКомментарий: —"
    assert _extract_file_id_from_bot_message_text(text) == "BAADAgADbXXXXXXXXXXX"
