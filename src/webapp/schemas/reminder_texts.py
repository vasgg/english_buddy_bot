from typing import Type

from database.models.reminder_text_variant import ReminderTextVariant
from pydantic import BaseModel, ConfigDict, Field


class ReminderTextVariantSchema(BaseModel):
    id: int = Field(title="id")
    text: str | None = Field(title="Текст")

    model_config = ConfigDict(extra="allow", from_attributes=True)


class ReminderTextVariantTableSchema(ReminderTextVariantSchema):
    edit_button: str = Field("✏️", title=" ")
    minus_button: str = Field("➖", title=" ")

    model_config = ConfigDict(from_attributes=True)


def get_reminder_text_variant_data_model(data: ReminderTextVariant) -> Type[BaseModel]:
    class ReminderTextVariantDataModel(BaseModel):
        text: str = Field(
            initial=data.text,
            description="Введите текст уведомления. Обязательное поле.",
            format="textarea",
            title="text",
            rows=5,
            cols=None,
        )

        model_config = ConfigDict(extra="allow", from_attributes=True)

    return ReminderTextVariantDataModel


def get_new_reminder_text_variant_data_model() -> Type[BaseModel]:
    class NewReminderTextVariantDataModel(BaseModel):
        text: str = Field(
            description="Введите текст уведомления. Обязательное поле.",
            format="textarea",
            title="text",
            rows=5,
            cols=None,
        )

    return NewReminderTextVariantDataModel


class AddReminderTextVariantDataModel(BaseModel):
    text: str


class EditReminderTextVariantDataModel(BaseModel):
    text: str
