from sqlalchemy.orm import Mapped

from src.bot.database.models.base import Base
from src.bot.resources.enums import ReactionType


class Reaction(Base):
    __tablename__ = 'reactions'

    text: Mapped[str]
    type: Mapped[ReactionType]
