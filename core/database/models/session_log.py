from typing import Any

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models import Base


class SessionLog(Base):
    __tablename__ = "session_logs"
    __table_args__ = (UniqueConstraint('session_id', 'slide_id'), )

    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id"))
    data: Mapped[str]
    update: Mapped[dict[str, Any]] = mapped_column(JSON)
