from sqlalchemy.orm import Mapped

from core.database.models.base import Base
from core.resources.enums import LessonLevel


class Lesson(Base):
    __tablename__ = "lessons"

    title: Mapped[str]
    slide_amount: Mapped[int]
    level: Mapped[LessonLevel | None]
