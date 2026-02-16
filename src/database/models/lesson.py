from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base
from enums import LessonLevel, LessonStatus


class Lesson(Base):
    __tablename__ = "lessons"

    index: Mapped[int | None] = mapped_column(unique=True)
    title: Mapped[str] = mapped_column(default="NEW LESSON TEMPLATE", server_default="NEW LESSON TEMPLATE")
    # TODO: maybe not opt
    level: Mapped[LessonLevel | None]
    path: Mapped[str | None]
    path_extra: Mapped[str | None]
    errors_threshold: Mapped[int | None]
    is_active: Mapped[LessonStatus] = mapped_column(default=LessonStatus.EDITING, server_default="EDITING")
    is_paid: Mapped[bool] = mapped_column(default=False, server_default="0")
