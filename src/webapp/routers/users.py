import logging
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent
from fastui.forms import fastui_form

from database.crud.user import get_user_from_db_by_id
from enums import SelectOneEnum, UserSubscriptionType
from webapp.controllers.users import get_users_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.main_component import get_common_content
from webapp.schemas.user import EditUserModel, get_user_data_model

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def users_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('users router called')
    users = await get_users_table_content(db_session)
    return get_common_content(
        c.Paragraph(text=' '),
        c.Paragraph(text='⬜ нет доступа'),
        c.Paragraph(text='🟩 доступ активен'),
        c.Paragraph(text='🟥 доступ истёк'),
        c.Paragraph(text='🟨 нет доступа, интересовался'),
        c.Paragraph(text='⭐ доступ навсегда'),
        c.Paragraph(text=' '),
        c.Table(
            data=users,
            columns=[
                DisplayLookup(field='number', title=' ', table_width_percent=3),
                DisplayLookup(field='fullname', title='полное имя', table_width_percent=15),
                DisplayLookup(field='username', title='никнейм', table_width_percent=15),
                DisplayLookup(field='registration_date', title='зарегистрирован', table_width_percent=10),
                DisplayLookup(field='comment', title='комментарий', table_width_percent=20),
                DisplayLookup(field='subscription_expired_at', title='доступ истекает', table_width_percent=13),
                DisplayLookup(field='color_code', title=' ', table_width_percent=3),
                DisplayLookup(field='icon', table_width_percent=3, title=' ', on_click=GoToEvent(url='{link}')),
            ],
        ),
        title='Пользователи',
    )


@router.get("/edit/{user_id}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_user_page(user_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    user = await get_user_from_db_by_id(user_id, db_session)
    submit_url = f'/api/users/edit/{user_id}/'
    form = c.ModelForm(model=get_user_data_model(user), submit_url=submit_url)
    name = f'{user.fullname} | {user.username}' if user.username else user.fullname
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=''),
        form,
        title=f'edit | user {user.id} | {name}',
    )


@router.post('/edit/{user_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_user(
    user_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditUserModel, fastui_form(EditUserModel)],
):
    user = await get_user_from_db_by_id(user_id, db_session)
    user.comment = form.comment
    if form.select_single == SelectOneEnum.ALLTIME_ACCESS:
        user.subscription_status = UserSubscriptionType.UNLIMITED_ACCESS
        user.subscription_expired_at = None
    elif form.select_single == SelectOneEnum.MONTHLY_ACCESS:
        user.subscription_status = UserSubscriptionType.LIMITED_ACCESS
        user.subscription_expired_at = form.subscription_expired_at
    elif form.select_single == SelectOneEnum.NO_ACCESS:
        user.subscription_status = UserSubscriptionType.NO_ACCESS
        user.subscription_expired_at = None

    await db_session.flush()
    return [c.FireEvent(event=GoToEvent(url='/users'))]
