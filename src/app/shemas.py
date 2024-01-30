from pydantic import BaseModel


class CreateNewSlideBellow(BaseModel):
    slide_id: int


class SlideOrderItem(BaseModel):
    lesson_id: int
    slide_id: int
    next_slide: int | None = None


class SlideOrderUpdateRequest(BaseModel):
    slides: list[SlideOrderItem]
