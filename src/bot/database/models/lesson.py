from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.models.base import Base
from bot.resources.enums import LessonLevel


class Lesson(Base):
    __tablename__ = 'lessons'

    title: Mapped[str]
    level: Mapped[LessonLevel | None]
    first_slide_id: Mapped[int] = mapped_column(ForeignKey('slides.id'))
    exam_slide_id: Mapped[int | None] = mapped_column(ForeignKey('slides.id'))
    is_paid: Mapped[bool] = mapped_column(default=False, server_default='0')
    total_slides: Mapped[int]
