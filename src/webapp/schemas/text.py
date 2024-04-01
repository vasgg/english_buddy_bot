from typing import Type

from database.models.text import Text
from pydantic import BaseModel, ConfigDict, Field


class TextsSchema(BaseModel):
    id: int
    description: str | None = Field(title='description')
    text: str | None = Field(title='text')

    model_config = ConfigDict(extra='allow', from_attributes=True)


class TextsTableSchema(TextsSchema):
    edit_button: str = Field("✏️", title=" ")
    minus_button: str = Field("➖", title=" ")

    model_config = ConfigDict(from_attributes=True)


def get_text_data_model(data: Text | None = None) -> Type[BaseModel]:
    class TextDataModel(BaseModel):
        description: str = Field(
            default=data.description if data else '',
            description='Введите описание. Обязательное поле.',
            title='description',
        )
        text: str = Field(
            initial=data.text if data else '',
            description='Введите текст. Обязательное поле.',
            format='textarea',
            title='text',
            rows=5,
            cols=None,
        )

        model_config = ConfigDict(extra='allow', from_attributes=True)

    return TextDataModel


class EditTextDataModel(BaseModel):
    description: str
    text: str
