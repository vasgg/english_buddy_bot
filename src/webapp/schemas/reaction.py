from typing import Type

from pydantic import BaseModel, Field

from database.models.reaction import Reaction
from enums import ReactionType


class ReactionsSchema(BaseModel):
    id: int = Field(title='id')
    text: str | None = Field(title='Текст')

    class Config:
        from_attributes = True
        extra = 'allow'


class ReactionsTableSchema(ReactionsSchema):
    edit_button: str = Field("✏️", title=" ")
    minus_button: str = Field("➖", title=" ")

    class Config:
        from_attributes = True


class DeleteReaction(BaseModel):
    id: int = Field(title='id')

    class Config:
        from_attributes = True


def get_reaction_data_model(data: Reaction) -> Type[BaseModel]:
    class ReactionDataModel(BaseModel):
        type: ReactionType = Field(
            default=data.type,
            description='Тип ответа, для вызова реакции. Обязательное поле.',
            title='type',
        )
        text: str = Field(default=data.text, description='Введите текст реакции. Обязательное поле.', title='text')

        class Config:
            from_attributes = True
            extra = 'allow'

    return ReactionDataModel


class EditReactionDataModel(BaseModel):
    type: ReactionType
    text: str


def get_new_reaction_data_model(reaction_type: ReactionType) -> Type[BaseModel]:
    description = (
        'Введите текст реакции на неверный ответ. Обязательное поле.'
        if reaction_type == ReactionType.WRONG
        else 'Введите текст реакции на верный ответ. Обязательное поле.'
    )

    class NewReactionDataModel(BaseModel):
        text: str = Field(description=description, title='text')

    return NewReactionDataModel


class AddReactionDataModel(BaseModel):
    text: str
