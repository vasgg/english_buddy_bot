from pydantic import BaseModel, Field

from bot.resources.enums import SlideType


class StickerSlideData(BaseModel):
    next_slide: int | None = Field(
        None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
    )
    slide_type: SlideType = Field(description='Выберите тип слайда. Обязательное поле.', title='slide type')

    class Config:
        from_attributes = True
        extra = 'allow'
