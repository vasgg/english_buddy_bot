from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class UserCompleteLesson(Base):
    __tablename__ = "users_completed_lessons"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
