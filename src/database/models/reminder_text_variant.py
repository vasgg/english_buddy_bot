from database.models.base import Base
from sqlalchemy.orm import Mapped


class ReminderTextVariant(Base):
    __tablename__ = "reminder_text_variants"

    text: Mapped[str]
