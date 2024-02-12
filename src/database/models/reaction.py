from sqlalchemy.orm import Mapped

from bot.resources.enums import ReactionType
from database.models.base import Base


class Reaction(Base):
    __tablename__ = 'reactions'

    text: Mapped[str]
    type: Mapped[ReactionType]
