from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    ADMINS: list[int]
    DB_NAME: str
    db_echo: bool = True
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
