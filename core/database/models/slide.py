from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base
from core.resources.enums import KeyboardType, SlideType


class Slide(Base):
    __tablename__ = "slides"

    text: Mapped[str | None]
    picture: Mapped[str | None]
    delay: Mapped[int | None]  # TODO: сменить тип на float
    slide_type: Mapped[SlideType]
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    right_answers: Mapped[str | None]
    almost_right_answers: Mapped[str | None]
    right_answer_reply: Mapped[str | None]
    almost_right_answer_reply: Mapped[str | None]
    wrong_answer_reply: Mapped[str | None]
    keyboard_type: Mapped[KeyboardType | None]
    keyboard: Mapped[str | None]
