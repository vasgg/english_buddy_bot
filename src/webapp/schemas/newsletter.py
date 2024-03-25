from typing import Annotated, Type

from fastapi import UploadFile
from fastui.forms import FormFile
from pydantic import BaseModel, Field, ConfigDict


def get_newsletter_data_model() -> Type[BaseModel]:
    class NewsletterDataModel(BaseModel):
        text: str = Field(
            description='Введите текст. Обязательное поле.',
            format='textarea',
            title='Текст рассылки. Он будет отправлен всем пользователям, у которых включены уведомления.',
            rows=5,
            cols=None,
        )
        upload_new_picture: Annotated[UploadFile, FormFile(accept='image/*', max_size=10_000_000)] | None = Field(
            description='Загрузите картинку с вашего компьютера. Поддерживаются файлы размером до 10мб. Необязательное поле.',
            title='Тут можно добавить к рассылке картинку.',
        )

        model_config = ConfigDict(extra='allow', from_attributes=True)

    return NewsletterDataModel
