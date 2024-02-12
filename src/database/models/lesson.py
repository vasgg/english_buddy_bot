from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from bot.resources.enums import LessonLevel
from database.models.base import Base


class Lesson(Base):
    __tablename__ = 'lessons'

    index: Mapped[int | None] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(default='NEW LESSON TEMPLATE', server_default='NEW LESSON TEMPLATE')
    level: Mapped[LessonLevel | None]
    first_slide_id: Mapped[int | None] = mapped_column(ForeignKey('slides.id'))
    exam_slide_id: Mapped[int | None] = mapped_column(ForeignKey('slides.id'))
    is_paid: Mapped[bool] = mapped_column(default=False, server_default='0')
    total_slides: Mapped[int | None]
