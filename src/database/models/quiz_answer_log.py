from database.models.base import Base
from enums import SlideType
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class QuizAnswerLog(Base):
    __tablename__ = "quiz_answer_logs"

    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    slide_id: Mapped[int] = mapped_column(ForeignKey("slides.id", ondelete="CASCADE"))
    slide_type: Mapped[SlideType]
    is_correct: Mapped[bool]
