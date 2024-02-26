from datetime import datetime
from typing import Type

from pydantic import BaseModel, Field

from bot.resources.enums import LessonLevel
from database.models.lesson import Lesson


class LessonSchema(BaseModel):
    id: int | None = None
    index: int | None = Field(title=' ')
    title: str = Field(title='title')
    level: LessonLevel | None = None
    first_slide_id: int | None = Field(title='first slide id')
    exam_slide_id: int | None = Field(title='exam slide id')
    is_paid: bool = Field(title='is paid')
    total_slides: int | None = Field(title='total slides')
    created_at: datetime | None = None

    class Config:
        from_attributes = True
        extra = 'allow'


class LessonsTableSchema(LessonSchema):
    edit_button: str = Field("✏️", title=" ")
    up_button: str = Field("🔼", title=" ")
    down_button: str = Field("🔽", title=" ")
    plus_button: str = Field("➕", title=" ")

    class Config:
        from_attributes = True


def get_lesson_data_model(lesson: Lesson) -> Type[BaseModel]:
    class LessonDataModel(BaseModel):
        title: str = Field(
            lesson.title,
            description='Введите название урока. Обязательное поле.',
            title='title',
        )
        first_slide_id: int | None = Field(
            lesson.first_slide_id,
            description='Введите id первого слайда. Необязательное поле.',
            title='first slide',
        )
        exam_slide_id: int | None = Field(
            lesson.exam_slide_id,
            description='Введите id первого экзаменационного слайда. Необязательное поле.',
            title='exam slide',
        )
        total_slides: int | None = Field(
            lesson.total_slides,
            description='Введите общее количество слайдов в уроке. Необязательное поле.',
            title='total slides',
        )
        is_paid: bool | None = Field(
            lesson.is_paid,
            description='Отметьте, если этот урок платный.',
            title='is paid',
        )

    return LessonDataModel


class EditLessonDataModel(BaseModel):
    title: str
    first_slide_id: int | None = None
    exam_slide_id: int | None = None
    total_slides: int | None = None
    is_paid: bool | None = False
