from sqlalchemy.orm import Mapped

from database.models.base import Base
from enums import ReactionType


class Reaction(Base):
    __tablename__ = 'reactions'

    text: Mapped[str]
    type: Mapped[ReactionType]
