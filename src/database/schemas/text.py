from typing import Type

from pydantic import BaseModel, Field

from database.models.text import Text


class TextsSchema(BaseModel):
    id: int
    description: str | None = Field(title='description')
    text: str | None = Field(title='text')

    class Config:
        from_attributes = True
        extra = 'allow'


class TextsTableSchema(TextsSchema):
    edit_button: str = Field("✏️", title=" ")
    minus_button: str = Field("➖", title=" ")

    class Config:
        from_attributes = True


def get_text_data_model(data: Text) -> Type[BaseModel]:
    class TextDataModel(BaseModel):
        description: str = Field(
            default=data.description,
            description='Введите описание. Обязательное поле.',
            title='description',
        )
        text: str = Field(default=data.text, description='Введите текст. Обязательное поле.', title='text')

        class Config:
            from_attributes = True
            extra = 'allow'

    return TextDataModel


class EditTextDataModel(BaseModel):
    description: str
    text: str


class DeleteTextDataModel(BaseModel):
    confirmation: bool
