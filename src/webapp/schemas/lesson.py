from datetime import datetime
from typing import Type

from pydantic import BaseModel, ConfigDict, Field

from database.models.lesson import Lesson
from enums import LessonLevel, LessonStatus


class ActiveLessonsTableSchema(BaseModel):
    id: int | None = None
    index: int | None = Field(title=' ')
    title: str = Field(title='Название урока')
    level: LessonLevel | None = None
    total_slides: str | None = Field(' ', title='Основные слайды')
    extra_slides: str | None = Field(' ', title='Экстра слайды')
    is_paid: str = Field(' ', title='Платный урок')
    errors_threshold: str = Field(' ', title='Порог ошибок')
    slides: str = Field('📖', title=' ')
    edit_button: str = Field('✏️', title=' ')
    up_button: str = Field('🔼', title=' ')
    down_button: str = Field('🔽', title=' ')
    minus_button: str = Field('➖', title=' ')

    model_config = ConfigDict(from_attributes=True)


class EditingLessonsTableSchema(BaseModel):
    id: int | None = None
    title: str = Field(title='Название урока')
    level: LessonLevel | None = None
    created_at: datetime | None = None
    total_slides: str | None = Field(' ', title='Основные слайды')
    extra_slides: str | None = Field(' ', title='Экстра слайды')
    is_paid: str = Field(' ', title='Платный урок')
    errors_threshold: str = Field(' ', title='Порог ошибок')
    slides: str = Field('📖', title=' ')
    edit_button: str = Field('✏️', title=' ')
    minus_button: str = Field('➖', title=' ')
    placeholder: str = Field(' ', title=' ')

    model_config = ConfigDict(from_attributes=True)


def get_lesson_data_model(lesson: Lesson) -> Type[BaseModel]:
    class LessonDataModel(BaseModel):
        title: str = Field(
            lesson.title,
            description='Введите название урока. Обязательное поле.',
            title='название',
        )
        errors_threshold: int | None = Field(
            lesson.errors_threshold if lesson.errors_threshold else None,
            description='Выберите порог ошибок в процентах для показа экстра слайдов. Необязательное поле.',
            title='порог ошибок',
        )
        is_active: bool = Field(
            True if lesson.is_active == LessonStatus.ACTIVE else False,
            description='Отметьте, чтобы урок был виден в боте пользователям. Необязательное поле.',
            title='активный урок',
        )
        is_paid: bool = Field(
            bool(lesson.is_paid),
            description='Отметьте, если этот урок платный. Необязательное поле.',
            title='платный',
        )

    return LessonDataModel


def get_new_lesson_data_model() -> Type[BaseModel]:
    class LessonDataModel(BaseModel):
        title: str = Field(
            'New lesson',
            description='Введите название урока. Обязательное поле.',
            title='название',
        )
        errors_threshold: int | None = Field(
            None,
            description='Введите порог ошибок в процентах для показа экстра слайдов. Необязательное поле.',
            title='порог ошибок',
        )
        is_paid: bool = Field(
            False,
            description='Отметьте, если этот урок платный. Необязательное поле.',
            title='платный',
        )

    return LessonDataModel


class EditLessonDataModel(BaseModel):
    title: str
    total_slides: int | None = None
    errors_threshold: int | None = None
    is_active: bool = False
    is_paid: bool | None = None


class NewLessonDataModel(BaseModel):
    title: str
    errors_threshold: int | None = None
    is_active: bool = False
    is_paid: bool | None = None
