from fastui import AnyComponent, components as c
from fastui.events import GoToEvent


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
