from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base
from core.resources.enums import SlideType


class Slide(Base):
    __tablename__ = "slides"
    # TODO: кажется тоже optional
    text: Mapped[str]
    picture: Mapped[str | None]
    keyboard: Mapped[str | None]
    slide_type: Mapped[SlideType]
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    right_answer: Mapped[str | None]
    almost_right_answer: Mapped[str | None]
    right_answer_reply: Mapped[str | None]
    almost_right_answer_reply: Mapped[str | None]
    wrong_answer_reply: Mapped[str | None]
