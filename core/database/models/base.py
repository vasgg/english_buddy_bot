from datetime import datetime
from typing import Any

from sqlalchemy import JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True
    
    # TODO: убрать
    __table_args__ = {"extend_existing": True}
    type_annotation_map = {
        dict[str, Any]: JSON
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow(), server_default=func.now())
