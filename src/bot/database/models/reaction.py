from sqlalchemy.orm import Mapped

from bot.database.models.base import Base
from bot.resources.enums import ReactionType


class Reaction(Base):
    __tablename__ = 'reactions'

    text: Mapped[str]
    type: Mapped[ReactionType]
