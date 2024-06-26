from database.models.base import Base
from enums import StickerType
from sqlalchemy.orm import Mapped, mapped_column


class Sticker(Base):
    __tablename__ = 'stickers'

    sticker_id: Mapped[str] = mapped_column(unique=True)
    sticker_type: Mapped[StickerType]
