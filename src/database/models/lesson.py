from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import LessonLevel


class Lesson(Base):
    __tablename__ = 'lessons'

    index: Mapped[int | None] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(default='NEW LESSON TEMPLATE', server_default='NEW LESSON TEMPLATE')
    # TODO: maybe not opt
    level: Mapped[LessonLevel | None]
    path: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True, server_default='1')
