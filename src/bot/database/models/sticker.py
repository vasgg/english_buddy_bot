from sqlalchemy.orm import Mapped, mapped_column

from src.bot.database.models.base import Base
from src.bot.resources.enums import StickerType


class Sticker(Base):
    __tablename__ = 'stickers'

    sticker_id: Mapped[str] = mapped_column(unique=True)
    sticker_type: Mapped[StickerType]
