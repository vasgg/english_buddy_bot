from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import SessionStartsFrom, SessionStatus


class Session(Base):
    __tablename__ = "sessions"

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    path: Mapped[str]
    path_extra: Mapped[str | None]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    current_step: Mapped[int] = mapped_column(default=0, server_default="0")
    starts_from: Mapped[SessionStartsFrom] = mapped_column()
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.IN_PROGRESS)
    in_extra: Mapped[bool] = mapped_column(default=False, server_default="0")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def get_path(self):
        if self.in_extra:
            return [int(elem) for elem in self.path_extra.split(".")]
        return [int(elem) for elem in self.path.split(".")]

    # noinspection PyTypeChecker
    def set_extra(self):
        self.in_extra = True
        self.current_step = 0

    def get_slide(self):
        return self.get_path()[self.current_step]

    def has_next(self):
        path = self.get_path()
        if self.current_step < len(path):
            return True
        return False
