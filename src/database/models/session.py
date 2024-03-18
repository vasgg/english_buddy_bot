from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import SessionStartsFrom, SessionStatus


class Session(Base):
    __tablename__ = 'sessions'

    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id'))
    path: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    current_slide_id: Mapped[int] = mapped_column(ForeignKey('slides.id', ondelete='CASCADE'))
    current_step: Mapped[int] = mapped_column(default=1, server_default='1')
    starts_from: Mapped[SessionStartsFrom] = mapped_column()
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.IN_PROGRESS)
