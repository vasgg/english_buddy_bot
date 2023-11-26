from sqlalchemy.orm import Mapped

from core.database.models.base import Base
from core.resources.enums import LessonLevel


class Lesson(Base):
    __tablename__ = "lessons"
    # TODO: кажется не None
    title: Mapped[str]
    slide_amount: Mapped[int | None]
    level: Mapped[LessonLevel | None]
