from datetime import datetime

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.models.base import Base


class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    username: Mapped[str | None] = mapped_column(String(32))
    paywall_access: Mapped[bool] = mapped_column(default=False, server_default='0')
    reminder_freq: Mapped[int | None]
    last_reminded_at: Mapped[datetime]

    def __str__(self):
        return (
            f'{self.__class__.__name__}(id={self.id}, '
            f'telegram_id={self.telegram_id}, first_name={self.first_name})'
        )

    def __repr__(self):
        return str(self)
