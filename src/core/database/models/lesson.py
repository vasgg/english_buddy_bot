from sqlalchemy.orm import Mapped

from core.database.models.base import Base
from core.resources.enums import LessonLevel, SlideType


class Lesson(Base):
    __tablename__ = "lessons"
    # TODO: выбрасываем exam_slide_type, добавляем поле total_lesson_slides
    # TODO: add FK to first_slide_id and first_slide_id

    title: Mapped[str]
    level: Mapped[LessonLevel | None]
    first_slide_id: Mapped[int]
    exam_slide_id: Mapped[int | None]
    exam_slide_type: Mapped[SlideType | None]
    # TODO: сюда пишем только количество слайдов с викторинами!
    # total_lesson_quiz_slides: Mapped[int]
