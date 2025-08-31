from datetime import date, datetime, timezone
from typing import Type

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

from database.models.user import User
from enums import SelectOneEnum, sub_status_to_select_one


class UsersSchema(BaseModel):
    id: int
    number: int
    fullname: str
    username: str | None
    credentials: str
    color_code: str
    icon: str
    link: str
    subscription_expired_at: str
    comment: str
    registration_date: str

    model_config = ConfigDict(extra='allow', from_attributes=True)


class EditUserModel(BaseModel):
    select_single: SelectOneEnum = Field(title='Выберите тип подписки')
    subscription_expired_at: date | None = Field(
        default=None,
        description='Введите дату и время окончания подписки. Необязательное поле.',
        title='дата истечения подписки',
    )
    comment: str | None = Field(
        default=None,
        description='Введите комментарий к пользователю. Необязательное поле.',
        format='textarea',
        rows=3,
        cols=None,
        title='комментарий',
    )

    # noinspection PyMethodParameters
    @field_validator('subscription_expired_at')
    def date_validator(cls, value: date | None) -> date | None:
        if value is None:
            return value
        if value <= datetime.now(timezone.utc).date():
            raise PydanticCustomError(
                'date_error',
                'Дата истечения подписки не может быть меньше или равна текущей дате',
            )
        return value


def get_user_data_model(user: User = None) -> Type[BaseModel]:
    class UserDataModel(BaseModel):
        select_single: SelectOneEnum = Field(
            default=sub_status_to_select_one(user.subscription_status), title='Выберите тип подписки'
        )
        subscription_expired_at: date | None = Field(
            default=user.subscription_expired_at if user.subscription_expired_at else None,
            description='Введите дату и время окончания подписки. Необязательное поле.',
            title='дата истечения подписки',
        )
        comment: str | None = Field(
            initial=user.comment if user else '',
            description='Введите комментарий к пользователю. Необязательное поле.',
            format='textarea',
            rows=3,
            cols=None,
            title='комментарий',
        )

    return UserDataModel


class SendMessageModel(BaseModel):
    message: str = Field(
        title='Текст сообщения',
        description='Введите текст, который будет отправлен пользователю в Telegram',
        format='textarea',
        rows=6,
    )
