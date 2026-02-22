from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from webapp.schemas.lesson import ActiveLessonsTableSchema, EditingLessonsTableSchema
from webapp.schemas.reaction import ReactionsTableSchema
from webapp.schemas.reminder_texts import ReminderTextVariantTableSchema
from webapp.schemas.slide import SlidesTableSchema


def get_active_lesson_table(lessons: list[dict]) -> c.Table:
    return c.Table(
        data=lessons,
        data_model=ActiveLessonsTableSchema,
        no_data_message="Нет активных уроков",
        columns=[
            DisplayLookup(
                field="index",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="title",
            ),
            DisplayLookup(
                field="total_slides",
                table_width_percent=8,
            ),
            DisplayLookup(
                field="extra_slides",
                table_width_percent=8,
            ),
            DisplayLookup(
                field="errors_threshold",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="is_paid",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="up_button",
                on_click=GoToEvent(url="/lessons/up_button/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="down_button",
                on_click=GoToEvent(url="/lessons/down_button/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="slides",
                on_click=GoToEvent(url="/slides/lesson{id}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="edit_button",
                on_click=GoToEvent(url="/lessons/edit/active/{id}/?index={index}"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="minus_button",
                on_click=GoToEvent(url="/lessons/confirm_delete/{id}/"),
                table_width_percent=3,
            ),
        ],
    )


def get_editing_lesson_table(lessons: list[dict]) -> c.Table:
    return c.Table(
        data=lessons,
        data_model=EditingLessonsTableSchema,
        no_data_message="Нет уроков в режиме редактирования",
        columns=[
            DisplayLookup(
                field="placeholder",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="title",
            ),
            DisplayLookup(
                field="total_slides",
                table_width_percent=8,
            ),
            DisplayLookup(
                field="extra_slides",
                table_width_percent=8,
            ),
            DisplayLookup(
                field="errors_threshold",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="is_paid",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="placeholder",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="placeholder",
                table_width_percent=3,
            ),
            DisplayLookup(
                field="slides",
                on_click=GoToEvent(url="/slides/lesson{id}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="edit_button",
                on_click=GoToEvent(url="/lessons/edit/editing/{id}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="minus_button",
                on_click=GoToEvent(url="/lessons/confirm_delete/{id}/"),
                table_width_percent=3,
            ),
        ],
    )


def get_reactions_table(reactions: list[dict]) -> c.Table:
    return c.Table(
        data=reactions,
        data_model=ReactionsTableSchema,
        no_data_message="Нет реакций",
        columns=[
            DisplayLookup(field="text", title="text"),
            DisplayLookup(
                field="edit_button",
                title=" ",
                on_click=GoToEvent(url="/reactions/edit/{id}"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="minus_button",
                title=" ",
                on_click=GoToEvent(url="/reactions/confirm_delete/{id}/"),
                table_width_percent=3,
            ),
        ],
    )


def get_reminder_texts_table(variants: list[dict]) -> c.Table:
    return c.Table(
        data=variants,
        data_model=ReminderTextVariantTableSchema,
        no_data_message="Нет вариантов текста",
        columns=[
            DisplayLookup(field="text", title="text"),
            DisplayLookup(
                field="edit_button",
                title=" ",
                on_click=GoToEvent(url="/reminder_texts/edit/{id}"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="minus_button",
                title=" ",
                on_click=GoToEvent(url="/reminder_texts/confirm_delete/{id}/"),
                table_width_percent=3,
            ),
        ],
    )


def get_slides_table(slides: list[dict]) -> c.Table:
    return c.Table(
        data=slides,
        data_model=SlidesTableSchema,
        no_data_message="Слайды не найдены",
        columns=[
            DisplayLookup(field="index", table_width_percent=3),
            DisplayLookup(field="id", title="id", table_width_percent=8),
            DisplayLookup(field="emoji", table_width_percent=3),
            DisplayLookup(field="text"),
            DisplayLookup(field="delay", table_width_percent=2),
            DisplayLookup(field="details", table_width_percent=20),
            DisplayLookup(field="is_exam_slide", table_width_percent=3),
            DisplayLookup(
                field="edit_button",
                on_click=GoToEvent(url="/slides/edit/regular/{slide_type}/{id}/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="up_button",
                on_click=GoToEvent(url="/slides/up/regular/{lesson_id}/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="down_button",
                on_click=GoToEvent(url="/slides/down/regular/{lesson_id}/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="plus_button",
                on_click=GoToEvent(url="/slides/plus_button/regular/{lesson_id}/?index={index}"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="minus_button",
                on_click=GoToEvent(url="/slides/confirm_delete/regular/{lesson_id}/{index}/"),
                table_width_percent=3,
            ),
        ],
    )


def get_extra_slides_table(slides: list[dict]) -> c.Table:
    return c.Table(
        data=slides,
        data_model=SlidesTableSchema,
        no_data_message="Экстра-слайды не найдены",
        columns=[
            DisplayLookup(field="index", table_width_percent=3),
            DisplayLookup(field="id", title="id", table_width_percent=8),
            DisplayLookup(field="emoji", table_width_percent=3),
            DisplayLookup(field="text"),
            DisplayLookup(field="delay", table_width_percent=2),
            DisplayLookup(field="details", table_width_percent=23),
            DisplayLookup(
                field="edit_button",
                on_click=GoToEvent(url="/slides/edit/extra/{slide_type}/{id}/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="up_button",
                on_click=GoToEvent(url="/slides/up/extra/{lesson_id}/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="down_button",
                on_click=GoToEvent(url="/slides/down/extra/{lesson_id}/{index}/"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="plus_button",
                on_click=GoToEvent(url="/slides/plus_button/extra/{lesson_id}/?index={index}"),
                table_width_percent=3,
            ),
            DisplayLookup(
                field="minus_button",
                on_click=GoToEvent(url="/slides/confirm_delete/extra/{lesson_id}/{index}/"),
                table_width_percent=3,
            ),
        ],
    )
