from sqlalchemy.orm import Mapped, mapped_column

from bot.resources.enums import StickerType
from database.models.base import Base


class Sticker(Base):
    __tablename__ = 'stickers'

    sticker_id: Mapped[str] = mapped_column(unique=True)
    sticker_type: Mapped[StickerType]
