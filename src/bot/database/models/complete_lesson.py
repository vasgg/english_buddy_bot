from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.models.base import Base


class CompleteLesson(Base):
    __tablename__ = 'completed_lessons'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id', ondelete='CASCADE'))
    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'))
