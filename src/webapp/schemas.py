from pydantic import BaseModel

from bot.resources.enums import KeyboardType, LessonLevel, SlideType


class CreateNewLessonRequest(BaseModel):
    lesson_id: int


class CreateNewSlideRequest(BaseModel):
    lesson_id: int
    slide_type: SlideType
    slide_id: int | None = None


class SlideOrderItem(BaseModel):
    slide_id: int
    lesson_id: int
    next_slide_id: int | None = None


class SlideOrderUpdateRequest(BaseModel):
    slides: list[SlideOrderItem]


class LessonOrderItem(BaseModel):
    lesson_id: int
    lesson_index: int


class LessonOrderUpdateRequest(BaseModel):
    lessons: list[LessonOrderItem]


class LessonData(BaseModel):
    id: int
    index: int | None = None
    title: str
    level: LessonLevel | None = None
    first_slide_id: int | None = None
    exam_slide_id: int | None = None
    is_paid: bool = False
    total_slides: int | None = None


class SlideData(BaseModel):
    slide_id: int
    next_slide: int | None = None
    text: str | None = None
    delay: float | None = None
    keyboard_type: KeyboardType | None = None
    keyboard: str | None = None
    picture: str | None = None
    right_answers: str | None = None
    almost_right_answers: str | None = None
    almost_right_answer_reply: str | None = None
    is_exam_slide: bool = False
    further_button: bool | None = None