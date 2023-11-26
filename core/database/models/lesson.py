from sqlalchemy.orm import Mapped

from core.database.models.base import Base
from core.resources.enums import LessonLevel


class Lesson(Base):
    __tablename__ = "lessons"
    # TODO: переделать slide_amount и exam_slide, убрать Optional
    title: Mapped[str]
    slide_amount: Mapped[int | None]
    level: Mapped[LessonLevel | None]
    exam_slide: Mapped[int | None]
