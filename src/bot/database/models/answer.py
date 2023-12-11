from sqlalchemy.orm import Mapped

from bot.database.models.base import Base
from bot.resources.enums import AnswerType


class Answer(Base):
    __tablename__ = "answers"

    text: Mapped[str]
    answer_type: Mapped[AnswerType]
