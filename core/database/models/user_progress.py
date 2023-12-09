from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class UserProgress(Base):
    __tablename__ = "users_progress"
    __table_args__ = (UniqueConstraint("user_id", "current_lesson"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    current_lesson: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE")
    )
    current_slide: Mapped[int] = mapped_column(
        ForeignKey("slides.id", ondelete="CASCADE"), default=1, server_default="1"
    )
    wrong_answer_attempts: Mapped[int | None]
    # __tablename__ = "users_progress"
    # __table_args__ = (UniqueConstraint('user_id', 'lesson_id'), )
    #
    # session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    # user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    # current_slide: Mapped[int] = mapped_column(ForeignKey("slides.id"), default=1, server_default='1')
    #
    # def __str__(self):
    #     return f'{self.__class__.__name__}(id={self.id}, user_id={self.user_id}, current_lesson={self.lesson_id})'
    #
    # def __repr__(self):
    #     return str(self)
