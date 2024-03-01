from typing import Annotated, Type

from fastapi import UploadFile
from fastui.forms import FormFile
from pydantic import BaseModel, Field

from bot.resources.enums import KeyboardType
from database.models.slide import Slide


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


def get_text_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class TextSlideDataModel(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide,
            description='Введите айди следующего за этим слайда. Необязательное поле.',
            title='next slide',
        )
        text: str | None = Field(
            slide.text,
            description='Введите текст слайда. Необязательное поле.',
            title='text',
        )
        delay: float | None = Field(
            slide.delay,
            description='Введите задержку после слайда (например, 1 секунда). Необязательное поле.',
            title='delay',
        )
        keyboard_type: KeyboardType | None = Field(
            slide.keyboard_type,
            description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
            title='keyboard type',
        )

    return TextSlideDataModel


def get_image_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class ImageSlideData(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide,
            description='Введите айди следующего за этим слайда. Необязательное поле.',
            title='next slide',
        )
        delay: float | None = Field(
            slide.delay,
            description='Введите задержку после слайда (например, 1 секунда). Необязательное поле.',
            title='delay',
        )
        keyboard_type: KeyboardType | None = Field(
            slide.keyboard_type,
            description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
            title='keyboard type',
        )
        select_picture: str | None = Field(
            slide.picture,
            description='Выберите изображение из папки с загруженными изображениями этого урока. Необязательное поле.',
            title='select picture',
            json_schema_extra={'search_url': f'/api/files/{slide.lesson_id}/'},
        )
        upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None = Field(
            description='Загрузите файл с вашего копьютера. Поддерживаются только изображения размером до 10мб.',
            title='upload new picture',
        )

        class Config:
            from_attributes = True
            extra = 'allow'

    return ImageSlideData


def get_pin_dict_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class PinDictSlideDataModel(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide,
            description='Введите айди следующего за этим слайда. Необязательное поле.',
            title='next slide',
        )
        text: str | None = Field(
            slide.text,
            description='Введите текст слайда, который будет прикреплён, как словарик урока. Необязательное поле.',
            title='text',
        )

        class Config:
            from_attributes = True
            extra = 'allow'

    return PinDictSlideDataModel


def get_quiz_options_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class QuizOptionsSlideDataModel(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide,
            description='Введите айди следующего за этим слайда. Необязательное поле.',
            title='next slide',
        )
        text: str | None = Field(slide.text, description='Введите текст вопроса. Обязательное поле.', title='text')
        right_answers: str | None = Field(
            slide.right_answers, description='Введите правильный ответ. Обязательное поле.', title='right answer'
        )
        keyboard: str | None = Field(
            slide.keyboard,
            description='Введите варианты ответов, разделённые "|". Один из них должен совпадать с полем "right answer". Обязательное поле.',
            title='Варианты ответов',
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide, description='Поставьте эту галочку, если это вопрос с экзамена', title='exam slide'
        )

        class Config:
            from_attributes = True
            extra = 'allow'

    return QuizOptionsSlideDataModel


def get_quiz_input_word_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class QuizInputWordSlideDataModel(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide,
            description='Введите айди следующего за этим слайда. Необязательное поле.',
            title='next slide',
        )
        text: str | None = Field(
            slide.text, description='Введите текст вопроса с пропущенным словом, отмеченным "…"', title='text'
        )
        right_answers: str | None = Field(
            slide.right_answers, description='Введите правильный ответ', title='right answer'
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide, description='Поставьте эту галочку, если это вопрос с экзамена', title='exam slide'
        )

        class Config:
            from_attributes = True
            extra = 'allow'

    return QuizInputWordSlideDataModel


def get_quiz_input_phrase_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class QuizInputPhraseSlideDataModel(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide,
            description='Введите айди следующего за этим слайда. Необязательное поле.',
            title='next slide',
        )
        text: str | None = Field(
            slide.text, description='Введите фразу на русском для перевода на английский', title='text'
        )
        right_answers: str | None = Field(
            slide.right_answers, description='Введите правильные ответы, разделённые "|"', title='right answers'
        )
        almost_right_answers: str | None = Field(
            slide.almost_right_answers,
            description='Введите почти правильные ответы, разделённые "|"',
            title='almost right answers',
        )
        almost_right_answer_reply: str | None = Field(
            slide.almost_right_answer_reply,
            description='Введите реплику на почти правильный ответ',
            title='almost right answer reply',
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide, description='Отметьте эту опцию, если это вопрос с экзамена', title='exam slide'
        )

        class Config:
            from_attributes = True
            extra = 'allow'

    return QuizInputPhraseSlideDataModel


def get_final_slide_slide_data_model(slide: Slide) -> Type[BaseModel]:
    class FinalSlideSlideDataModel(BaseModel):
        next_slide: int | None = Field(
            slide.next_slide, description='Айди следующего за этим слайда. Необязательное поле.', title='next slide'
        )
        text: str | None = Field(slide.text, description='Введите текст финального слайда', title='text')

        class Config:
            from_attributes = True
            extra = 'allow'

    return FinalSlideSlideDataModel


class EditTextSlideDataModel(BaseModel):
    next_slide: int | None = None
    text: str | None
    delay: float | None = None
    keyboard_type: KeyboardType | None = None


class EditDictSlideData(BaseModel):
    next_slide: int | None = None
    text: str | None = None


class EditQuizOptionsSlideData(BaseModel):
    next_slide: int | None = None
    text: str | None
    right_answers: str | None
    keyboard: str | None
    is_exam_slide: bool = False


class EditQuizInputWordSlideData(BaseModel):
    next_slide: int | None = None
    text: str | None
    right_answers: str | None
    is_exam_slide: bool = False


class EditQuizInputPhraseSlideData(BaseModel):
    next_slide: int | None = None
    text: str | None
    right_answers: str | None
    almost_right_answers: str | None
    almost_right_answer_reply: str | None
    is_exam_slide: bool = False


class EditFinalSlideSlideData(BaseModel):
    next_slide: int | None = None
    text: str | None


class EditImageSlideData(BaseModel):
    next_slide: int | None = None
    delay: float | None = None
    keyboard_type: KeyboardType | None = None
    select_picture: str | None = None
    upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None = None
