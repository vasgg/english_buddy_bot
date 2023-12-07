from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base
from core.resources.enums import LessonLevel


class Lesson(Base):
    __tablename__ = "lessons"

    title: Mapped[str]
    level: Mapped[LessonLevel | None]
    first_slide_id: Mapped[int]
    exam_slide_id: Mapped[int | None]
