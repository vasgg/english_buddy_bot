from typing import Annotated, Type

from fastapi import UploadFile
from fastui.forms import FormFile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from database.models.slide import Slide
from enums import KeyboardType


class SlidesSchema(BaseModel):
    id: int
    text: str | None = Field(title='Контент')
    details: str | None = Field(title='Контекст')
    is_exam_slide: str = Field(title=' ')

    model_config = ConfigDict(extra='allow', from_attributes=True)


class SlidesTableSchema(SlidesSchema):
    index: int = Field(title=' ')
    lesson_id: int = Field(title=' ')
    slide_type: str = Field(title=' ')
    emoji: str = Field(title=' ')
    edit_button: str = Field(title=' ')
    up_button: str = Field(title=' ')
    down_button: str = Field(title=' ')
    plus_button: str = Field(title=' ')
    minus_button: str = Field(title=' ')

    model_config = ConfigDict(from_attributes=True)


def get_text_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class TextSlideDataModel(BaseModel):
        text: str = Field(
            initial=slide.text if slide else '',
            description='Введите текст слайда. Обязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='текст слайда',
        )
        delay: float | None = Field(
            slide.delay if slide else None,
            description='Введите задержку после слайда (например, 1 секунда). Необязательное поле.',
            title='задержка',
        )
        keyboard_type: bool | None = Field(
            bool(slide and slide.keyboard_type == KeyboardType.FURTHER),
            description='Если под слайдом нужна кнопка далее, поставьте галочку. Необязательное поле.',
            title='Кнопка "далее"',
        )

    return TextSlideDataModel


def get_image_slide_data_model(slide: Slide = None, lesson_id: int = None) -> Type[BaseModel]:
    class ImageSlideData(BaseModel):
        select_picture: str | None = Field(
            slide.picture if slide else None,
            description='Выберите изображение из папки с загруженными изображениями этого урока. Необязательное поле.',
            title='выбор картинки из загруженных',
            json_schema_extra={'search_url': f'/api/files/{lesson_id if lesson_id else slide.lesson_id}/'},
        )
        upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None = Field(
            description='Загрузите файл с вашего компьютера. Поддерживаются только изображения до 10мб. Необязательное поле.',
            title='загрузка картинки',
        )
        delay: float | None = Field(
            slide.delay if slide else None,
            description='Введите задержку после слайда (например, 1 секунда). Необязательное поле.',
            title='задержка',
        )
        keyboard_type: bool | None = Field(
            bool(slide and slide.keyboard_type == KeyboardType.FURTHER),
            description='Если под слайдом нужна кнопка далее, поставьте галочку. Необязательное поле.',
            title='Кнопка "далее"',
        )

    return ImageSlideData


def get_pin_dict_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class PinDictSlideDataModel(BaseModel):
        text: str = Field(
            initial=slide.text if slide else '',
            description='Введите текст слайда, который будет прикреплён, как словарик урока. Обязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='текст слайда',
        )

    return PinDictSlideDataModel


def get_quiz_options_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class QuizOptionsSlideDataModel(BaseModel):
        text: str = Field(
            slide.text if slide else '',
            description='Введите текст вопроса с пропущенным словом, отмеченным "_". Обязательное поле.',
            title='текст вопроса',
        )
        right_answers: str = Field(
            slide.right_answers if slide else '',
            description='Введите правильный ответ. Обязательное поле.',
            title='правильный ответ',
        )
        keyboard: str = Field(
            slide.keyboard if slide else '',
            description='Введите варианты неправильных ответов, разделённые "|". '
            'Квиз будет составлен из неправильных вариантов + правильный ответ. Обязательное поле.',
            title='неправильные ответы',
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide if slide else False,
            description='Поставьте эту галочку, если это вопрос с экзамена. Необязательное поле.',
            title='exam slide',
        )

    return QuizOptionsSlideDataModel


def get_quiz_input_word_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class QuizInputWordSlideDataModel(BaseModel):
        text: str = Field(
            initial=slide.text if slide else '',
            description='Введите текст вопроса с пропущенным словом, отмеченным "_". Обязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='текст вопроса',
        )
        right_answers: str = Field(
            slide.right_answers if slide else None,
            description='Введите правильный ответ. Обязательное поле.',
            title='правильный ответ',
        )
        almost_right_answers: str | None = Field(
            initial=slide.almost_right_answers if slide else '',
            description='Введите почти правильные ответы, разделённые "|". Необязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='почти правильные ответы',
        )
        almost_right_answer_reply: str | None = Field(
            initial=slide.almost_right_answer_reply if slide else None,
            description='Введите реплику на почти правильный ответ. Необязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='реплика на почти правильный ответ.',
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide if slide else False,
            description='Поставьте эту галочку, если это вопрос с экзамена. Необязательное поле.',
            title='exam slide',
        )

    return QuizInputWordSlideDataModel


def get_quiz_input_phrase_slide_data_model(slide: Slide = None) -> Type[BaseModel]:
    class QuizInputPhraseSlideDataModel(BaseModel):
        text: str = Field(
            initial=slide.text if slide else '',
            description='Введите фразу на русском для перевода на английский. Обязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='текст вопроса',
        )
        right_answers: str = Field(
            initial=slide.right_answers if slide else '',
            description='Введите правильные ответы, разделённые "|". Обязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='правильные ответы',
        )
        almost_right_answers: str | None = Field(
            initial=slide.almost_right_answers if slide else '',
            description='Введите почти правильные ответы, разделённые "|". Необязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='почти правильные ответы',
        )
        almost_right_answer_reply: str | None = Field(
            initial=slide.almost_right_answer_reply if slide else None,
            description='Введите реплику на почти правильный ответ. Необязательное поле.',
            format='textarea',
            rows=5,
            cols=None,
            title='реплика на почти правильный ответ.',
        )
        is_exam_slide: bool = Field(
            slide.is_exam_slide if slide else False,
            description='Отметьте эту опцию, если это вопрос с экзамена. Необязательное поле.',
            title='exam slide',
        )

    return QuizInputPhraseSlideDataModel


def get_delete_slide_confirmation_data_model(slide: Slide = None) -> Type[BaseModel]:
    class DeleteSlideConfirmationDataModel(BaseModel):
        confirm: bool = Field(False, description=f'Вы действительно хотите удалить слайд {slide.id}?', title='Confirm')

    return DeleteSlideConfirmationDataModel


class EditTextSlideDataModel(BaseModel):
    text: str
    delay: float | None = None
    keyboard_type: bool = False


class EditDictSlideData(BaseModel):
    text: str


class EditQuizOptionsSlideData(BaseModel):
    text: str
    right_answers: str
    keyboard: str
    is_exam_slide: bool = False

    # noinspection PyMethodParameters
    @field_validator('text')
    def text_validator(cls, value: str) -> str:
        if '_' not in value:
            raise PydanticCustomError(
                'missing_symbol',
                'Текст вопроса должен содержать символ "_" для подстановки правильного значения.',
            )
        return value


class EditQuizInputWordSlideData(BaseModel):
    text: str
    right_answers: str
    almost_right_answers: str | None = None
    almost_right_answer_reply: str | None = None
    is_exam_slide: bool = False

    # noinspection PyMethodParameters
    @field_validator('text')
    def text_validator(cls, value: str) -> str:
        if '_' not in value:
            raise PydanticCustomError(
                'missing_symbol',
                'Текст вопроса должен содержать символ "_" для подстановки правильного значения.',
            )
        return value


class EditQuizInputPhraseSlideData(BaseModel):
    text: str
    right_answers: str
    almost_right_answers: str | None = None
    almost_right_answer_reply: str | None = None
    is_exam_slide: bool = False


class EditImageSlideData(BaseModel):
    delay: float | None = None
    select_picture: str | None = None
    keyboard_type: bool = False
    upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None
