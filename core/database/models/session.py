from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models import Base
from core.resources.enums import SessionStatus, SessonStartsFrom


class Session(Base):
    __tablename__ = "sessions"

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    current_slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id"))
    starts_from: Mapped[SessonStartsFrom] = mapped_column()
    status: Mapped[SessionStatus] = mapped_column(default=SessionStatus.IN_PROGRESS)
