from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.models.base import Base
from bot.resources.enums import SlideType


class SessionLog(Base):
    __tablename__ = 'session_logs'

    session_id: Mapped[int] = mapped_column(ForeignKey('sessions.id', ondelete='CASCADE'))
    slide_id: Mapped[int] = mapped_column(ForeignKey('slides.id', ondelete='CASCADE'))
    slide_type: Mapped[SlideType]
    data: Mapped[str | None]
    is_correct: Mapped[bool | None]
    update: Mapped[dict[str, Any]] = mapped_column(JSON)
