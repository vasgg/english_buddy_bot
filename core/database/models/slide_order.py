from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class SlideOrder(Base):
    __tablename__ = "slides_order"

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), unique=True)
    slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id", ondelete="CASCADE"), unique=True)
    slide_number: Mapped[int]
