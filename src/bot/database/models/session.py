from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.models.base import Base
from bot.resources.enums import SessionStartsFrom, SessionStatus


class Session(Base):
    __tablename__ = "sessions"

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    current_slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id"))
    starts_from: Mapped[SessionStartsFrom] = mapped_column()
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.IN_PROGRESS)
