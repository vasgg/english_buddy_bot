from typing import Type

from pydantic import BaseModel, Field

from database.models.slide import Slide


# class StickerSlideData(BaseModel):
#     next_slide: int | None = Field(
#         None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
#     )
#     # slide_type: SlideType = Field(description='Выберите тип слайда. Обязательное поле.', title='slide type')
#
#     class Config:
#         from_attributes = True
#         extra = 'allow'


def get_sticker_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class StickerSlideDataModel(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide,
            description='Введите айди следующего за этим слайда. Необязательное поле.',
            title='next slide',
        )

        class Config:
            from_attributes = True
            extra = 'allow'

    return StickerSlideDataModel


class EditStickerSlideDataModel(BaseModel):
    next_slide: int | None
