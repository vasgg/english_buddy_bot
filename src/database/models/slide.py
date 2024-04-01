from database.models.base import Base
from enums import KeyboardType, SlideType
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class Slide(Base):
    __tablename__ = 'slides'

    text: Mapped[str | None]
    picture: Mapped[str | None]
    delay: Mapped[float | None]
    slide_type: Mapped[SlideType]
    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id'))
    right_answers: Mapped[str | None]
    almost_right_answers: Mapped[str | None]
    almost_right_answer_reply: Mapped[str | None]
    keyboard_type: Mapped[KeyboardType | None]
    keyboard: Mapped[str | None]
    is_exam_slide: Mapped[bool] = mapped_column(default=False, server_default='0')
