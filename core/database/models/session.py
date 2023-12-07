from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models import Base
from core.resources.enums import SessionStatus, SessonStartsFrom


class Session(Base):
    __tablename__ = "sessions"
    # TODO: add constraint for unique user_id, lesson_id where status = IN PROGRESS
    # __table_args__ = (UniqueConstraint('user_id', 'current_lesson'), )

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    current_slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id"))
    starts_from: Mapped[SessonStartsFrom] = mapped_column(default=SessonStartsFrom.BEGIN)
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.IN_PROGRESS)
