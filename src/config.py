from functools import lru_cache
from logging.handlers import RotatingFileHandler

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from enums import Stage


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    ADMIN: int
    SUB_ADMINS: list[int]
    TEACHERS: list[int]
    DATABASE_URL: SecretStr
    SENTRY_AIOGRAM_DSN: SecretStr | None = None
    SENTRY_FASTAPI_DSN: SecretStr | None = None
    TOP_BAD_SLIDES_COUNT: int
    STAGE: Stage
    db_echo: bool = False
    REDIS_URL: str
    TASKIQ_REDIS_URL: str
    allowed_image_formats: list[str] = ["png", "jpg", "jpeg", "gif", "heic", "tiff", "webp"]

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL.get_secret_value()

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings():
    return Settings()


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
                "maxBytes": 50000000,
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
