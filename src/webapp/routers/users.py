import logging
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.events import GoToEvent
from fastui.forms import fastui_form
import arrow

from database.crud.user import get_user_from_db_by_id
from database.crud.lesson import (
    get_completed_lessons_recent_first,
    get_lesson_by_id,
)
from database.crud.session import get_in_progress_lessons_recent_first
from database.crud.slide import get_slide_by_id
from enums import SelectOneEnum, UserSubscriptionType, sub_status_to_select_one
from lesson_path import LessonPath
from webapp.controllers.users import get_users_table_content
from webapp.db import AsyncDBSession
from webapp.routers.components.buttons import back_button, create_send_message_button
from webapp.routers.components.components import get_common_content, get_users_page
from webapp.schemas.user import EditUserModel, SendMessageModel, get_user_data_model
from config import get_settings
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

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
    completed_lessons_ids = await get_completed_lessons_recent_first(user_id=user.id, db_session=db_session)
    lesson_components: list[AnyComponent] = []
    for lesson_id, last_completed_at in completed_lessons_ids:
        lesson = await get_lesson_by_id(lesson_id=lesson_id, db_session=db_session)
        if not lesson or not getattr(lesson, 'title', None):
            continue
        humanized = arrow.get(last_completed_at).humanize(locale='ru')
        lesson_components.append(c.Paragraph(text=f"{lesson.title} — {humanized}"))
    if not lesson_components:
        lesson_components = [c.Paragraph(text='У пользователя нет пройденных уроков')]
    info_block: list[AnyComponent] = [
        c.Heading(text='Пройденные уроки:', level=5),
        c.Paragraph(text=''),
    ] + lesson_components + [
        c.Paragraph(text=''),
    ]
    in_progress_components: list[AnyComponent] = []
    in_progress = await get_in_progress_lessons_recent_first(user.id, db_session)
    for session in in_progress:
        lesson = await get_lesson_by_id(lesson_id=session.lesson_id, db_session=db_session)
        if not lesson or not getattr(lesson, 'title', None):
            continue

        humanized_started = arrow.get(session.created_at).humanize(locale='ru')
        current_slide_id: int | None
        try:
            current_slide_id = session.get_slide()
        except Exception:
            current_slide_id = None

        lesson_path_str = lesson.path_extra if session.in_extra else lesson.path
        lesson_path = LessonPath(lesson_path_str).path
        slide_index_in_lesson: int | None = None
        if current_slide_id is not None:
            with suppress(ValueError):
                slide_index_in_lesson = lesson_path.index(current_slide_id) + 1

        slide = await get_slide_by_id(current_slide_id, db_session) if current_slide_id is not None else None
        source = 'extra' if session.in_extra else 'regular'
        slide_url = (
            f'/slides/edit/{source}/{slide.slide_type}/{current_slide_id}/{slide_index_in_lesson}/'
            if slide and slide_index_in_lesson is not None
            else f'/slides/lesson{lesson.id}/'
        )
        slide_id_component: AnyComponent
        if current_slide_id is None:
            slide_id_component = c.Text(text='—')
        else:
            slide_id_component = c.Link(
                components=[c.Text(text=str(current_slide_id))],
                on_click=GoToEvent(url=slide_url),
            )
        in_progress_components.append(
            c.Div(
                class_name='+ d-flex flex-wrap align-items-baseline gap-1',
                components=[
                    c.Text(text=f"{lesson.title} — {humanized_started} — слайд {slide_index_in_lesson or '—'} (id:"),
                    slide_id_component,
                    c.Text(text=')'),
                ],
            ),
        )
    if not in_progress_components:
        in_progress_components = [c.Paragraph(text='Нет начатых, но не завершённых уроков')]
    in_progress_block: list[AnyComponent] = [
        c.Heading(text='Начатые, но не завершённые уроки:', level=5),
        c.Paragraph(text=''),
    ] + in_progress_components + [
        c.Paragraph(text=''),
    ]
    submit_url = f'/api/users/edit/{user_id}/'
    form = c.ModelForm(model=get_user_data_model(user), submit_url=submit_url)
    name = f'{user.fullname} | {user.username}' if user.username else user.fullname
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=GoToEvent(url='/users')),
        c.Paragraph(text=''),
        create_send_message_button(user.id),
        c.Paragraph(text=''),
        *info_block,
        *in_progress_block,
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


@router.get('/send_message/{user_id}/', response_model=FastUI, response_model_exclude_none=True)
async def send_message_page(
    user_id: int,
    db_session: AsyncDBSession,
    error: str | None = None,
    status: str | None = None,
) -> list[AnyComponent]:
    user = await get_user_from_db_by_id(user_id, db_session)
    form = c.ModelForm(model=SendMessageModel, submit_url=f'/api/users/send_message/{user_id}/')
    title = f"send message | user {user.id} | {user.fullname}"
    warn_components: list[AnyComponent] = []
    if not getattr(user, 'telegram_id', None):
        warn_components.append(
            c.Paragraph(text='⚠️ У пользователя отсутствует telegram_id — отправка невозможна')
        )
    messages: list[AnyComponent] = []
    if status == 'sent':
        messages.append(c.Paragraph(text='✅ Сообщение успешно отправлено'))
    if error == 'forbidden':
        messages.append(c.Paragraph(text='❌ Бот заблокирован пользователем. Сообщение не доставлено.'))
    if error == 'notelegram':
        messages.append(c.Paragraph(text='❌ У пользователя отсутствует telegram_id — сообщение не отправлено'))
    if error == 'unknown':
        messages.append(c.Paragraph(text='❌ Произошла ошибка при отправке сообщения'))
    nav_components: list[AnyComponent] = []
    if status == 'sent' or error in {'forbidden', 'notelegram', 'unknown'}:
        nav_components.append(
            c.Link(
                components=[c.Button(text='Назад', named_style='secondary')],
                on_click=GoToEvent(url=f'/users/edit/{user_id}/'),
            )
        )
    hide_top_back = status == 'sent' or error in {'forbidden', 'notelegram', 'unknown'}
    return get_common_content(
        *([] if hide_top_back else [back_button, c.Paragraph(text='')]),
        c.Paragraph(text=f"Получатель: {user.fullname} (@{user.username})" if user.username else f"Получатель: {user.fullname}"),
        c.Paragraph(text=f"telegram_id: {getattr(user, 'telegram_id', '—')}"),
        *messages,
        *nav_components,
        *warn_components,
        c.Paragraph(text=''),
        form,
        title=title,
    )


@router.post('/send_message/{user_id}/', response_model=FastUI, response_model_exclude_none=True)
async def send_message(
    user_id: int,
    db_session: AsyncDBSession,
    form: Annotated[SendMessageModel, fastui_form(SendMessageModel)],
) -> list[AnyComponent]:
    user = await get_user_from_db_by_id(user_id, db_session)
    settings = get_settings()
    if not getattr(user, 'telegram_id', None):
        return [c.FireEvent(event=GoToEvent(url=f'/users/send_message/{user_id}/?error=notelegram'))]
    try:
        async with Bot(
            token=settings.BOT_TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        ) as bot:
            await bot.send_message(chat_id=user.telegram_id, text=form.message)
    except TelegramForbiddenError:
        return [c.FireEvent(event=GoToEvent(url=f'/users/send_message/{user_id}/?error=forbidden'))]
    except Exception:
        return [c.FireEvent(event=GoToEvent(url=f'/users/send_message/{user_id}/?error=unknown'))]
    return [c.FireEvent(event=GoToEvent(url=f'/users/send_message/{user_id}/?status=sent'))]
