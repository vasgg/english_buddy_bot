from datetime import date, datetime

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import UserSubscriptionType


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    fullname: Mapped[str]
    username: Mapped[str | None] = mapped_column(String(32))
    reminder_freq: Mapped[int | None]
    last_reminded_at: Mapped[datetime]
    # noinspection PyTypeChecker
    subscription_status: Mapped[UserSubscriptionType] = mapped_column(
        default=UserSubscriptionType.NO_ACCESS, server_default=UserSubscriptionType.NO_ACCESS.value
    )
    subscription_expired_at: Mapped[date | None]
    comment: Mapped[str | None]

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, telegram_id={self.telegram_id}, fullname={self.fullname})"

    def __repr__(self):
        return str(self)
