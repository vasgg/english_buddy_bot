from database.models.base import Base
from enums import ReactionType
from sqlalchemy.orm import Mapped


class Reaction(Base):
    __tablename__ = 'reactions'

    text: Mapped[str]
    type: Mapped[ReactionType]
