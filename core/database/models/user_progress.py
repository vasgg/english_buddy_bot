from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class UserProgress(Base):
    __tablename__ = "users_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    current_lesson: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    current_slide: Mapped[int] = mapped_column(ForeignKey("slides.id", ondelete="CASCADE"), default=1)
