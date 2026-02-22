from fastui import AnyComponent
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from pydantic import BaseModel, Field

from enums import SlidesMenuType
from webapp.routers.components.buttons import back_button
from webapp.schemas.statistics import SessionsStatisticsTableSchema, SlidesStatisticsTableSchema
from webapp.schemas.text import TextsTableSchema
from webapp.schemas.user import UsersSchema

try:
    c.AnyComponent = AnyComponent  # type: ignore[attr-defined]
    for model in (
        c.ModelForm,
        c.Table,
        c.PageTitle,
        c.Navbar,
        c.Page,
        c.Paragraph,
        c.Heading,
        c.Button,
        c.Text,
        c.Link,
    ):
        model.model_rebuild()
    DisplayLookup.model_rebuild()
except Exception:
    pass


def get_common_content(
    *components: AnyComponent,
    title: str | None = None,
) -> list[AnyComponent]:
    return [
        c.PageTitle(text=f"English buddy — {title}" if title else "admin panel"),
        c.Navbar(
            start_links=[
                c.Link(
                    components=[c.Text(text="Уроки")],
                    on_click=GoToEvent(url="/lessons"),
                ),
                c.Link(
                    components=[c.Text(text="Тексты")],
                    on_click=GoToEvent(url="/texts"),
                ),
                c.Link(
                    components=[c.Text(text="Напоминания")],
                    on_click=GoToEvent(url="/reminder_texts"),
                ),
                c.Link(
                    components=[c.Text(text="Реакции")],
                    on_click=GoToEvent(url="/reactions"),
                ),
                c.Link(
                    components=[c.Text(text="Настройки уведомлений")],
                    on_click=GoToEvent(url="/notifications"),
                ),
                c.Link(
                    components=[c.Text(text="Пользователи")],
                    on_click=GoToEvent(url="/users"),
                ),
                c.Link(
                    components=[c.Text(text="Статистика")],
                    on_click=GoToEvent(url="/statistics"),
                ),
            ],
        ),
        c.Page(
            components=[
                *((c.Heading(text=title),) if title else ()),
                *components,
            ],
        ),
    ]


def get_add_slide_page(lesson_id: int, source: SlidesMenuType, index: int | None = None) -> list[AnyComponent]:
    suffix = f"{index}/" if index else ""
    return get_common_content(
        c.Paragraph(text=""),
        c.Paragraph(text="Выберите тип слайда."),
        c.Paragraph(text=""),
        c.Button(
            text="🖋  текст",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/text/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        c.Button(
            text="🖼  картинка",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/image/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        c.Button(
            text="📎  словарик",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/pin_dict/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        c.Button(
            text="🧨  малый стикер",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/small_sticker/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        c.Button(
            text="💣  большой стикер",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/big_sticker/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        c.Button(
            text="🧩  квиз варианты",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/quiz_options/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        c.Button(
            text="🗨  квиз впиши слово",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/quiz_input_word/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        c.Button(
            text="💬  квиз впиши фразу",
            on_click=GoToEvent(url=f"/slides/new/{lesson_id}/{source}/quiz_input_phrase/" + suffix),
            class_name="+ ms-2",
            named_style="secondary",
        ),
        c.Paragraph(text=""),
        back_button,
        title="Добавить новый слайд",
    )


def get_statistics_page(users_count: int, rows: list[dict], errors_stats: list[dict]) -> list[AnyComponent]:
    return get_common_content(
        c.Heading(text="Пользователи", level=4),
        c.Paragraph(text=f"Всего пользователей: {users_count}"),
        c.Heading(text="Сессии", level=4),
        c.Table(
            data=rows,
            data_model=SessionsStatisticsTableSchema,
            columns=[
                DisplayLookup(field="description", title="описание"),
                DisplayLookup(field="value", title="значение", table_width_percent=38),
            ],
        ),
        c.Heading(text="Топ слайдов по количеству ошибок", level=4),
        c.Paragraph(text=" "),
        c.Table(
            data=errors_stats,
            data_model=SlidesStatisticsTableSchema,
            no_data_message="Нет данных по ошибкам",
            columns=[
                DisplayLookup(field="slide_type", table_width_percent=3, title=" "),
                DisplayLookup(field="is_exam_slide", table_width_percent=3, title=" "),
                DisplayLookup(field="slide_id", title="номер слайда", table_width_percent=24),
                DisplayLookup(field="lesson_title", title="название урока", table_width_percent=25),
                DisplayLookup(field="count_correct", title="всего правильных", table_width_percent=10),
                DisplayLookup(field="count_wrong", title="всего неправильных", table_width_percent=10),
                DisplayLookup(field="correctness_rate", title="процент правильных", table_width_percent=10),
                DisplayLookup(
                    field="icon",
                    table_width_percent=3,
                    title=" ",
                    on_click=GoToEvent(url="{link}"),
                ),
            ],
        ),
        title="Статистика",
    )


def get_texts_page(texts: list[dict]) -> list[AnyComponent]:
    return get_common_content(
        c.Paragraph(text=""),
        c.Table(
            data=texts,
            data_model=TextsTableSchema,
            no_data_message="Тексты не найдены",
            columns=[
                DisplayLookup(field="description", title="description"),
                DisplayLookup(field="text", title="text"),
                DisplayLookup(
                    field="edit_button",
                    title=" ",
                    on_click=GoToEvent(url="/texts/edit/{id}"),
                    table_width_percent=3,
                ),
            ],
        ),
        c.Paragraph(text=""),
        title="Тексты",
    )


class FilterForm(BaseModel):
    user: str = Field(json_schema_extra={"search_url": "/api/forms/search", "placeholder": "Поиск пользователя..."})


def get_users_page(users: list[dict], filter_form_initial: dict, blocked_users_count: int) -> list[AnyComponent]:
    return get_common_content(
        c.Paragraph(text=" "),
        c.Paragraph(text="⬜ нет доступа"),
        c.Paragraph(text="🟩 доступ активен"),
        c.Paragraph(text="🟥 доступ истёк"),
        c.Paragraph(text="🟨 нет доступа, интересовался"),
        c.Paragraph(text="⭐ доступ навсегда"),
        c.Paragraph(text=f"🚫 заблокировали бота: {blocked_users_count}"),
        c.Paragraph(text=" "),
        c.ModelForm(
            model=FilterForm,
            submit_url=".",
            initial=filter_form_initial,
            method="GOTO",
            submit_on_change=True,
            display_mode="inline",
        ),
        c.Table(
            data=users,
            data_model=UsersSchema,
            no_data_message="Пользователи не найдены",
            columns=[
                DisplayLookup(field="number", title=" ", table_width_percent=3),
                DisplayLookup(field="fullname", title="полное имя", table_width_percent=15),
                DisplayLookup(field="username", title="никнейм", table_width_percent=15),
                DisplayLookup(field="registration_date", title="зарегистрирован", table_width_percent=10),
                DisplayLookup(field="comment", title="комментарий", table_width_percent=20),
                DisplayLookup(field="subscription_expired_at", title="доступ истекает", table_width_percent=13),
                DisplayLookup(field="bot_blocked_icon", title="блок", table_width_percent=3),
                DisplayLookup(field="color_code", title=" ", table_width_percent=3),
                DisplayLookup(field="icon", table_width_percent=3, title=" ", on_click=GoToEvent(url="{link}")),
            ],
        ),
        title="Пользователи",
    )
