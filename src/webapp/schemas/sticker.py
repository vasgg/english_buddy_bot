from typing import Type

from database.models.slide import Slide
from enums import SlideType, StickerType
from pydantic import BaseModel, ConfigDict, Field


def get_sticker_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    s_type = StickerType.BIG if slide.slide_type == SlideType.BIG_STICKER else StickerType.SMALL

    class StickerSlideDataModel(BaseModel):
        sticker_type: StickerType = Field(
            s_type if slide else None,
            description="Выберите тип стикера. Обязательное поле.",
            title="sticker type",
        )

        model_config = ConfigDict(from_attributes=True)

    return StickerSlideDataModel


class EditStickerSlideDataModel(BaseModel):
    sticker_type: StickerType
