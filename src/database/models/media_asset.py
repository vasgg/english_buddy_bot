from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    file_id: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str | None] = mapped_column(String(512))
    file_extension: Mapped[str | None] = mapped_column(String(32))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    file_unique_id: Mapped[str | None] = mapped_column(String(512))
