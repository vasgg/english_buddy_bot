from logging.handlers import RotatingFileHandler

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    ADMINS: list[int]
    DB_NAME: str
    SENTRY_AIOGRAM_DSN: SecretStr
    SENTRY_FASTAPI_DSN: SecretStr
    db_echo: bool = False
    allowed_MIME_types_to_upload: list[str] = [
        'image/png',
        'image/jpeg',
        'image/gif',
        'image/heic',
        'image/tiff',
        'image/webp',
    ]

    @property
    def aiosqlite_db_url(self) -> str:
        return f'sqlite+aiosqlite:///{self.DB_NAME}.db'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()


def get_logging_config(app_name: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "main": {
                "format": "%(asctime)s|%(levelname)s|%(module)s|%(funcName)s: %(message)s",
                "datefmt": "%d.%m.%Y %H:%M:%S%z",
            },
            "errors": {
                "format": "%(asctime)s|%(levelname)s|%(module)s|%(funcName)s|L%(lineno)d: %(message)s",
                "datefmt": "%d.%m.%Y %H:%M:%S%z",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "main",
                "stream": "ext://sys.stdout",
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "errors",
                "stream": "ext://sys.stderr",
            },
            "file": {
                "()": RotatingFileHandler,
                "level": "INFO",
                "formatter": "main",
                "filename": f"logs/{app_name}_log.log",
                "maxBytes": 500000,
                "backupCount": 3,
            },
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["stdout", "stderr", "file"],
            },
        },
    }
