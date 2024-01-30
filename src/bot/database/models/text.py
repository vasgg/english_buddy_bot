from sqlalchemy.orm import Mapped, mapped_column

from src.bot.database.models.base import Base


class Text(Base):
    __tablename__ = 'texts'

    prompt: Mapped[str] = mapped_column(unique=True)
    text: Mapped[str]
    description: Mapped[str]
