from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    ADMINS: list[int]
    DB_NAME: str
    db_echo: bool = True
    allowed_image_formats: list[str] = ['png', 'jpg', 'jpeg', 'heic', 'gif', 'webp']

    @property
    def aiosqlite_db_url(self) -> str:
        return f'sqlite+aiosqlite:///{self.DB_NAME}.db'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
