from datetime import datetime
from typing import Type

from pydantic import BaseModel, Field

from database.models.lesson import Lesson
from enums import LessonLevel


class LessonSchema(BaseModel):
    id: int | None = None
    index: int | None = Field(title=' ')
    title: str = Field(title='title')
    level: LessonLevel | None = None
    exam_slide_id: int | None = Field(title='exam slide id')
    created_at: datetime | None = None

    class Config:
        from_attributes = True
        extra = 'allow'


class LessonsTableSchema(LessonSchema):
    total_slides: str | None = Field(' ', title='total slides')
    is_paid: str = Field(' ', title='is paid')
    slides: str = Field('📖', title=' ')
    edit_button: str = Field('✏️', title=' ')
    up_button: str = Field('🔼', title=' ')
    down_button: str = Field('🔽', title=' ')
    plus_button: str = Field('➕', title=' ')

    class Config:
        from_attributes = True


def get_lesson_data_model(lesson: Lesson) -> Type[BaseModel]:
    class LessonDataModel(BaseModel):
        title: str = Field(
            lesson.title,
            description='Введите название урока. Обязательное поле.',
            title='title',
        )
        exam_slide_id: int | None = Field(
            lesson.exam_slide_id,
            description='Введите id первого экзаменационного слайда. Необязательное поле.',
            title='exam slide',
        )
        is_paid: bool | None = Field(
            True if lesson.path.split('.')[0] == '1' else False,
            description='Отметьте, если этот урок платный. Необязательное поле.',
            title='is paid',
        )

    return LessonDataModel


def get_new_lesson_data_model() -> Type[BaseModel]:
    class LessonDataModel(BaseModel):
        title: str = Field(
            'New lesson',
            description='Введите название урока. Обязательное поле.',
            title='title',
        )
        is_paid: bool | None = Field(
            False,
            description='Отметьте, если этот урок платный. Необязательное поле.',
            title='is paid',
        )

    return LessonDataModel


class EditLessonDataModel(BaseModel):
    title: str
    first_slide_id: int | None = None
    exam_slide_id: int | None = None
    total_slides: int | None = None
    is_paid: bool | None = False


class NewLessonDataModel(BaseModel):
    title: str
    is_paid: bool | None = False
