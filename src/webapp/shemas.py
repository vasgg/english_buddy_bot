from pydantic import BaseModel

from bot.resources.enums import SlideType


class CreateNewSlideBellow(BaseModel):
    slide_type: SlideType
    slide_id: int


class SlideOrderItem(BaseModel):
    slide_id: int
    lesson_id: int
    next_slide_id: int | None = None


class SlideOrderUpdateRequest(BaseModel):
    slides: list[SlideOrderItem]
