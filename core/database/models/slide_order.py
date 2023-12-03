from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class SlideOrder(Base):
    __tablename__ = "slides_order"
    __table_args__ = (UniqueConstraint('lesson_id', 'slide_id'),)

    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id", ondelete="CASCADE"))
    slide_index: Mapped[int] = mapped_column(unique=True)
