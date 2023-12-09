from sqlalchemy.orm import Mapped

from core.database.models.base import Base
from core.resources.enums import AnswerType


class Answer(Base):
    __tablename__ = "answers"

    text: Mapped[str]
    answer_type: Mapped[AnswerType]
