from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent


def get_active_lesson_table(lessons: list[dict]) -> c.Table:
    return c.Table(
        data=lessons,
        columns=[
            DisplayLookup(
                field='index',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='title',
            ),
            DisplayLookup(
                field='total_slides',
                table_width_percent=8,
            ),
            DisplayLookup(
                field='extra_slides',
                table_width_percent=8,
            ),
            DisplayLookup(
                field='errors_threshold',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='is_paid',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='up_button',
                on_click=GoToEvent(url='/lessons/up_button/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='down_button',
                on_click=GoToEvent(url='/lessons/down_button/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='slides',
                on_click=GoToEvent(url='/slides/lesson{id}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='edit_button',
                on_click=GoToEvent(url='/lessons/edit/active/{id}/?index={index}'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/lessons/confirm_delete/{id}/'),
                table_width_percent=3,
            ),
        ],
    )


def get_editing_lesson_table(lessons: list[dict]) -> c.Table:
    return c.Table(
        data=lessons,
        columns=[
            DisplayLookup(
                field='placeholder',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='title',
            ),
            DisplayLookup(
                field='total_slides',
                table_width_percent=8,
            ),
            DisplayLookup(
                field='extra_slides',
                table_width_percent=8,
            ),
            DisplayLookup(
                field='errors_threshold',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='is_paid',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='placeholder',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='placeholder',
                table_width_percent=3,
            ),
            DisplayLookup(
                field='slides',
                on_click=GoToEvent(url='/slides/lesson{id}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='edit_button',
                on_click=GoToEvent(url='/lessons/edit/editing/{id}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/lessons/confirm_delete/{id}/'),
                table_width_percent=3,
            ),
        ],
    )


def get_reactions_table(reactions: list[dict]) -> c.Table:
    return c.Table(
        data=reactions,
        columns=[
            DisplayLookup(field='text', title='text'),
            DisplayLookup(
                field='edit_button',
                title=' ',
                on_click=GoToEvent(url='/reactions/edit/{id}'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                title=' ',
                on_click=GoToEvent(url='/reactions/confirm_delete/{id}/'),
                table_width_percent=3,
            ),
        ],
    )


def get_reminder_texts_table(variants: list[dict]) -> c.Table:
    return c.Table(
        data=variants,
        columns=[
            DisplayLookup(field='text', title='text'),
            DisplayLookup(
                field='edit_button',
                title=' ',
                on_click=GoToEvent(url='/reminder_texts/edit/{id}'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                title=' ',
                on_click=GoToEvent(url='/reminder_texts/confirm_delete/{id}/'),
                table_width_percent=3,
            ),
        ],
    )


def get_slides_table(slides: list[dict]) -> c.Table:
    return c.Table(
        data=slides,
        columns=[
            DisplayLookup(field='index', table_width_percent=3),
            DisplayLookup(field='emoji', table_width_percent=3),
            DisplayLookup(field='text'),
            DisplayLookup(field='delay', table_width_percent=2),
            DisplayLookup(field='details', table_width_percent=20),
            DisplayLookup(field='is_exam_slide', table_width_percent=3),
            DisplayLookup(
                field='edit_button',
                on_click=GoToEvent(url='/slides/edit/regular/{slide_type}/{id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='up_button',
                on_click=GoToEvent(url='/slides/up/regular/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='down_button',
                on_click=GoToEvent(url='/slides/down/regular/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='plus_button',
                on_click=GoToEvent(url='/slides/plus_button/regular/{lesson_id}/?index={index}'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/slides/confirm_delete/regular/{id}/{index}/'),
                table_width_percent=3,
            ),
        ],
    )


def get_extra_slides_table(slides: list[dict]) -> c.Table:
    return c.Table(
        data=slides,
        columns=[
            DisplayLookup(field='index', table_width_percent=3),
            DisplayLookup(field='emoji', table_width_percent=3),
            DisplayLookup(field='text'),
            DisplayLookup(field='delay', table_width_percent=2),
            DisplayLookup(field='details', table_width_percent=23),
            DisplayLookup(
                field='edit_button',
                on_click=GoToEvent(url='/slides/edit/extra/{slide_type}/{id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='up_button',
                on_click=GoToEvent(url='/slides/up/extra/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='down_button',
                on_click=GoToEvent(url='/slides/down/extra/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='plus_button',
                on_click=GoToEvent(url='/slides/plus_button/extra/{lesson_id}/?index={index}'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/slides/confirm_delete/extra/{id}/{index}/'),
                table_width_percent=3,
            ),
        ],
    )
