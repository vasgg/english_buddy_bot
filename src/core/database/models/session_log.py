from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base
from core.resources.enums import SlideType


class SessionLog(Base):
    __tablename__ = "session_logs"

    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id"))
    slide_type: Mapped[SlideType]
    data: Mapped[str | None]
    update: Mapped[dict[str, Any]] = mapped_column(JSON)
    # TODO: вместо него завести флаг right or wrong
