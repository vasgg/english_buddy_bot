from typing import Annotated, Type

from fastapi import UploadFile
from fastui.forms import FormFile
from pydantic import BaseModel, Field

from database.models.slide import Slide
from enums import KeyboardType


class SlidesSchema(BaseModel):
    id: int
    text: str | None = Field(title='content')
    details: str | None = Field(title='context')
    is_exam_slide: str = Field(title=' ')

    class Config:
        from_attributes = True
        extra = 'allow'


class SlidesTableSchema(SlidesSchema):
    index: int = Field(title=' ')
    emoji: str = Field(title=' ')
    edit_button: str = Field(title=' ')
    up_button: str = Field(title=' ')
    down_button: str = Field(title=' ')
    plus_button: str = Field(title=' ')
    minus_button: str = Field(title=' ')

    class Config:
        from_attributes = True


def get_text_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class TextSlideDataModel(BaseModel):
        text: str | None = Field(
            slide.text if slide else None,
            description='Введите текст слайда. Необязательное поле.',
            title='text',
        )
        delay: float | None = Field(
            slide.delay if slide else None,
            description='Введите задержку после слайда (например, 1 секунда). Необязательное поле.',
            title='delay',
        )
        keyboard_type: KeyboardType | None = Field(
            slide.keyboard_type if slide else None,
            description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
            title='keyboard type',
        )

    return TextSlideDataModel


def get_image_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class ImageSlideData(BaseModel):
        delay: float | None = Field(
            slide.delay if slide else None,
            description='Введите задержку после слайда (например, 1 секунда). Необязательное поле.',
            title='delay',
        )
        keyboard_type: KeyboardType | None = Field(
            slide.keyboard_type if slide else None,
            description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
            title='keyboard type',
        )
        select_picture: str | None = Field(
            slide.picture if slide else None,
            description='Выберите изображение из папки с загруженными изображениями этого урока. Необязательное поле.',
            title='select picture',
            json_schema_extra={'search_url': f'/api/files/{slide.lesson_id}/'},
        )
        upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None = Field(
            description='Загрузите файл с вашего копьютера. Поддерживаются только изображения размером до 10мб.',
            title='upload new picture',
        )

    return ImageSlideData


def get_pin_dict_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class PinDictSlideDataModel(BaseModel):
        text: str | None = Field(
            slide.text if slide else None,
            description='Введите текст слайда, который будет прикреплён, как словарик урока. Необязательное поле.',
            title='text',
        )

    return PinDictSlideDataModel


def get_quiz_options_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class QuizOptionsSlideDataModel(BaseModel):
        text: str | None = Field(
            slide.text if slide else None, description='Введите текст вопроса. Обязательное поле.', title='text'
        )
        right_answers: str | None = Field(
            slide.right_answers, description='Введите правильный ответ. Обязательное поле.', title='right answer'
        )
        keyboard: str | None = Field(
            slide.keyboard if slide else None,
            description='Введите варианты ответов, разделённые "|". Один из них должен совпадать с полем "right answer". Обязательное поле.',
            title='Варианты ответов',
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide if slide else False,
            description='Поставьте эту галочку, если это вопрос с экзамена',
            title='exam slide',
        )

    return QuizOptionsSlideDataModel


def get_quiz_input_word_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class QuizInputWordSlideDataModel(BaseModel):
        text: str | None = Field(
            slide.text if slide else None,
            description='Введите текст вопроса с пропущенным словом, отмеченным "…"',
            title='text',
        )
        right_answers: str | None = Field(
            slide.right_answers if slide else None, description='Введите правильный ответ', title='right answer'
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide if slide else False,
            description='Поставьте эту галочку, если это вопрос с экзамена',
            title='exam slide',
        )

    return QuizInputWordSlideDataModel


def get_quiz_input_phrase_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class QuizInputPhraseSlideDataModel(BaseModel):
        text: str | None = Field(
            slide.text if slide else None,
            description='Введите фразу на русском для перевода на английский',
            title='text',
        )
        right_answers: str | None = Field(
            slide.right_answers if slide else None,
            description='Введите правильные ответы, разделённые "|"',
            title='right answers',
        )
        almost_right_answers: str | None = Field(
            slide.almost_right_answers if slide else None,
            description='Введите почти правильные ответы, разделённые "|"',
            title='almost right answers',
        )
        almost_right_answer_reply: str | None = Field(
            slide.almost_right_answer_reply if slide else None,
            description='Введите реплику на почти правильный ответ',
            title='almost right answer reply',
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide if slide else False,
            description='Отметьте эту опцию, если это вопрос с экзамена',
            title='exam slide',
        )

    return QuizInputPhraseSlideDataModel


def get_final_slide_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class FinalSlideSlideDataModel(BaseModel):
        text: str | None = Field(
            slide.text if slide else None, description='Введите текст финального слайда', title='text'
        )

    return FinalSlideSlideDataModel


def get_delete_slide_confirmation_data_model(slide: Slide = None) -> Type[BaseModel]:
    class DeleteSlideConfirmationDataModel(BaseModel):
        confirm: bool = Field(False, description=f'Вы действительно хотите удалить слайд {slide.id}?', title='Confirm')

    return DeleteSlideConfirmationDataModel


class EditTextSlideDataModel(BaseModel):
    text: str | None = None
    delay: float | None = None
    keyboard_type: KeyboardType | None = None


class EditDictSlideData(BaseModel):
    text: str | None = None


class EditQuizOptionsSlideData(BaseModel):
    text: str | None = None
    right_answers: str | None = None
    keyboard: str | None = None
    is_exam_slide: bool = False


class EditQuizInputWordSlideData(BaseModel):
    text: str | None = None
    right_answers: str | None = None
    is_exam_slide: bool = False


class EditQuizInputPhraseSlideData(BaseModel):
    text: str | None = None
    right_answers: str | None = None
    almost_right_answers: str | None = None
    almost_right_answer_reply: str | None = None
    is_exam_slide: bool = False


class EditFinalSlideSlideData(BaseModel):
    text: str | None = None


class EditImageSlideData(BaseModel):
    delay: float | None = None
    keyboard_type: KeyboardType | None = None
    select_picture: str | None = None
    upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None = None


class DeleteSlideData(BaseModel):
    confirm: bool = False
