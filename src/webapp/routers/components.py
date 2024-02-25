from fastui import AnyComponent, components as c
from fastui.events import GoToEvent, PageEvent

from bot.resources.enums import DeletedObjectType


def get_common_content(
    *components: AnyComponent,
    title: str | None = None,
) -> list[AnyComponent]:
    return [
        c.PageTitle(text=f"English buddy — {title}" if title else "admin panel"),
        c.Navbar(
            # title="English buddy",
            # title_event=GoToEvent(url="/"),
            start_links=[
                c.Link(
                    components=[c.Text(text='Уроки')],
                    on_click=GoToEvent(url='/lessons'),
                    active='startswith:/lessons',
                ),
                c.Link(
                    components=[c.Text(text='Слайды')],
                    on_click=GoToEvent(url='/slides/lesson1'),
                    active='startswith:/slides',
                ),
                c.Link(
                    components=[c.Text(text='Тексты')],
                    on_click=GoToEvent(url='/texts'),
                    active='startswith:/texts',
                ),
                c.Link(
                    components=[c.Text(text='Реакции')],
                    on_click=GoToEvent(url='/reactions'),
                    active='startswith:/reactions',
                ),
            ],
        ),
        c.Page(
            components=[
                *((c.Heading(text=title),) if title else ()),
                *components,
            ],
        ),
        # c.Footer(
        #     extra_text="english buddy admin section",
        #     links=[
        #         c.Link(
        #             components=[c.Text(text="бот")],
        #             on_click=GoToEvent(url="https://t.me/english_buddy_bot"),
        #         ),
        #     ],
        # ),
    ]


def get_modal_confirmation(mode: DeletedObjectType, object_id: int) -> AnyComponent:
    match mode:
        case DeletedObjectType.REACTION:
            title = 'Удаление реакции'
            question = 'Вы уверены, что хотите удалить реакцию?'
            submit_url = '/api/delete/reactions/modal-prompt'
        case DeletedObjectType.SLIDE:
            title = 'Удаление слайда'
            question = 'Вы уверены, что хотите удалить слайд?'
            submit_url = '/api/delete/slide/modal-prompt'
        case _:
            assert False, f'Unknown mode: {mode}'
    return (
        c.Modal(
            title=title,
            body=[
                c.Paragraph(text=question),
                c.Form(
                    form_fields=[],
                    submit_url=submit_url,
                    loading=[c.Spinner(text='Удаление...')],
                    footer=[],
                    submit_trigger=PageEvent(name='modal-form-submit'),
                ),
            ],
            footer=[
                c.Button(text='Отмена', named_style='secondary', on_click=PageEvent(name='modal-prompt', clear=True)),
                c.Button(text='Удалить', named_style='danger', on_click=PageEvent(name='modal-form-submit')),
            ],
            open_trigger=PageEvent(name='modal-prompt'),
        ),
    )
