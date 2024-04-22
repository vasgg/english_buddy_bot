import logging
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from database.crud.user import get_user_from_db_by_id
from enums import SelectOneEnum, UserSubscriptionType
from webapp.controllers.users import get_users_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.buttons import back_button
from webapp.routers.components.components import get_common_content, get_users_page
from webapp.schemas.user import EditUserModel, get_user_data_model

router = APIRouter()
logger = logging.getLogger()


@router.get("", response_model=FastUI, response_model_exclude_none=True)
async def users_page(db_session: AsyncDBSession, user: str | None = None) -> list[AnyComponent]:
    logger.info('users router called')
    users = await get_users_table_content(db_session)
    filter_form_initial = {}
    if user:
        users = [u for u in users if user.lower() in u.credentials.lower()]
        filter_form_initial['users'] = {'value': user}
    return get_users_page(users, filter_form_initial)


@router.get("/edit/{user_id}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_user_page(user_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    user = await get_user_from_db_by_id(user_id, db_session)
    submit_url = f'/api/users/edit/{user_id}/'
    form = c.ModelForm(model=get_user_data_model(user), submit_url=submit_url)
    name = f'{user.fullname} | {user.username}' if user.username else user.fullname
    return get_common_content(
        back_button,
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
