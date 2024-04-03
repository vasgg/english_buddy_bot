from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import SessionStartsFrom, SessionStatus


class Session(Base):
    __tablename__ = 'sessions'

    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id'))
    path: Mapped[str]
    path_extra: Mapped[str | None]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    current_slide_id: Mapped[int] = mapped_column(ForeignKey('slides.id', ondelete='CASCADE'))
    current_step: Mapped[int] = mapped_column(default=1, server_default='1')
    starts_from: Mapped[SessionStartsFrom] = mapped_column()
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.IN_PROGRESS)
    in_extra: Mapped[bool] = mapped_column(default=False, server_default='0')

    def get_path(self):
        if self.in_extra:
            return [int(elem) for elem in self.path_extra.split(".")]
        return [int(elem) for elem in self.path.split(".")]

    def set_extra(self):
        self.in_extra = True
        self.current_step = 0

    def get_slide(self):
        if self.in_extra:
            return self.path_extra[self.current_step]
        return self.path[self.current_step]

    def has_next(self):
        path = self.get_path()
        if self.current_step < len(path):
            return True
        return False
