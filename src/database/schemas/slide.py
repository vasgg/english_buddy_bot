from typing import Annotated, Type

from fastapi import UploadFile
from fastui.forms import FormFile, Textarea
from pydantic import BaseModel, Field

from bot.resources.enums import KeyboardType
from database.models.slide import Slide


class SlidesSchema(BaseModel):
    id: int
    text: str | None = Field(title='content')
    details: str | None = Field(title='details')
    # slide_type: SlideType
    is_exam_slide: str = Field(title=' ')

    class Config:
        from_attributes = True
        extra = 'allow'


class SlidesTableSchema(SlidesSchema):
    index: int = Field(title=' ')
    emoji: str = Field(title=' ')
    edit_button: str = Field(title=" ")
    up_button: str = Field(title=" ")
    down_button: str = Field(title=" ")
    plus_button: str = Field(title=" ")
    minus_button: str = Field(title=" ")

    class Config:
        from_attributes = True


#

# class SlideSchema(BaseModel):
#     id: int = Field(title='id')
#     slide_type: SlideType = Field(title='slide type')
#     next_slide: int | None = Field(title='next slide')
#     text: str | None = Field(title='text')
#     picture: str | None = Field(title='picture')
#     delay: float | None = Field(title='delay')
#     lesson_id: int = Field(title='lesson id')
#     right_answers: str | None = Field(title='right answers')
#     almost_right_answers: str | None = Field(title='almost_right_answers')
#     almost_right_answer_reply: str | None = Field(title='almost_right_answer_reply')
#     keyboard_type: KeyboardType | None = Field(title='keyboard_type')
#     keyboard: str | None = Field(title='keyboard')
#     is_exam_slide: bool = Field(title='exam')
#
#     class Config:
#         from_attributes = True
#         extra = 'allow'


class TextSlideData(BaseModel):
    next_slide: int | None = Field(
        None,
        description='Введите айди следующего за этим слайда. Необязательное поле.',
        title='next slide',
    )
    text: Annotated[str, Textarea()] | None = Field(
        None, description='Введите текст слайда. Необязательное поле.', title='text'
    )
    delay: float | None = Field(
        None, description='Введите задержку после слайда (например, 0.1 секунды). Необязательное поле.', title='delay'
    )
    keyboard_type: KeyboardType | None = Field(
        None,
        description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
        title='keyboard type',
    )

    class Config:
        from_attributes = True
        extra = 'allow'


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
            description='Введите задержку после слайда (например, 0.1 секунды). Необязательное поле.',
            title='delay',
        )
        keyboard_type: KeyboardType | None = Field(
            slide.keyboard_type,
            description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
            title='keyboard type',
        )

    return TextSlideDataModel


class ShowImageSlideData(BaseModel):
    next_slide: int | None = Field(
        None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
    )
    picture: str | None = Field(None, title='picture')
    delay: float | None = Field(
        None, description='Введите задержку после слайда (например, 0.1 секунды). Необязательное поле.', title='delay'
    )
    keyboard_type: KeyboardType | None = Field(
        None,
        description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
        title='keyboard type',
    )

    class Config:
        from_attributes = True


def get_image_slide_data_model(lesson_id: int) -> Type[BaseModel]:
    class ImageSlideData(BaseModel):
        next_slide: int | None = Field(
            None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
        )
        delay: float | None = Field(
            None,
            description='Введите задержку после слайда (например, 0.1 секунды). Необязательное поле.',
            title='delay',
        )
        keyboard_type: KeyboardType | None = Field(
            # None,
            description='Если под слайдом нужна кнопка далее, выберите "FURTHER". Необязательное поле.',
            title='keyboard type',
        )
        select_picture: str | None = Field(
            None,
            description='Выберите изображение из папки с загруженными изображениями этого урока. Необязательное поле.',
            title='select picture',
            json_schema_extra={'search_url': f'/api/files/{lesson_id}/'},
        )
        upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None = Field(
            description='Загрузите файл с вашего копьютера. Поддерживаются только изображения размером до 10мб.',
            title='upload new picture',
        )

        class Config:
            from_attributes = True
            extra = 'allow'

    return ImageSlideData


class PinDictSlideData(BaseModel):
    next_slide: int | None = Field(
        None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
    )
    text: str | None = Field(
        None,
        description='Введите текст слайда, который будет прикреплён, как словарик урока. Необязательное поле.',
        title='text',
    )

    class Config:
        from_attributes = True
        extra = 'allow'


class QuizOptionsSlideData(BaseModel):
    next_slide: int | None = Field(
        None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
    )
    text: str | None = Field(description='Введите текст вопроса. Обязательное поле.', title='text')
    right_answers: str | None = Field(description='Введите правильный ответ. Обязательное поле.', title='right answer')
    keyboard: str | None = Field(
        description='Введите варианты ответов, разделённые "|". Один из них должен совпадать с полем "right answer". Обязательное поле.',
        title='Варианты ответов',
    )
    is_exam_slide: bool = Field(
        False, description='Отметьте эту опцию, если это вопрос с экзамена', title='exam slide'
    )

    class Config:
        from_attributes = True
        extra = 'allow'


class QuizInputWordSlideData(BaseModel):
    next_slide: int | None = Field(
        None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
    )
    text: str | None = Field(
        None, description='Введите текст вопроса с пропущенным словом, отмеченным "…"', title='text'
    )
    right_answers: str | None = Field(None, description='Введите правильный ответ', title='right answer')
    is_exam_slide: bool = Field(
        False, description='Отметьте эту опцию, если это вопрос с экзамена', title='exam slide'
    )

    class Config:
        from_attributes = True
        extra = 'allow'


class QuizInputPhraseSlideData(BaseModel):
    next_slide: int | None = Field(
        None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
    )
    text: str | None = Field(None, description='Введите фразу на русском для перевода на английский', title='text')
    right_answers: str | None = Field(
        None, description='Введите правильные ответы, разделённые "|"', title='right answers'
    )
    almost_right_answers: str | None = Field(
        None, description='Введите почти правильные ответы, разделённые "|"', title='almost right answers'
    )
    almost_right_answer_reply: str | None = Field(
        None, description='Введите реплику на почти правильный ответ', title='almost right answer reply'
    )
    is_exam_slide: bool = Field(
        False, description='Отметьте эту опцию, если это вопрос с экзамена', title='exam slide'
    )

    class Config:
        from_attributes = True
        extra = 'allow'


class FinalSlideSlideData(BaseModel):
    id: int = Field(title='id')
    next_slide: int | None = Field(
        None, description='Введите айди следующего за этим слайда. Необязательное поле.', title='next slide'
    )
    text: str | None = Field(title='text')

    class Config:
        from_attributes = True
        extra = 'allow'
