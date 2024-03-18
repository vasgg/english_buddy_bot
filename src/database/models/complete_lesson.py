from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from database.models.lesson import Lesson
from database.models.session import Session
from database.models.user import User


class CompleteLesson(Base):
    __tablename__ = 'completed_lessons'

    user_id: Mapped[int] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'))
    lesson_id: Mapped[int] = mapped_column(ForeignKey(Lesson.id, ondelete='CASCADE'))
    session_id: Mapped[int] = mapped_column(ForeignKey(Session.id, ondelete='CASCADE'))
