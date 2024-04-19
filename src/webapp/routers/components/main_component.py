from fastui import AnyComponent
from fastui import components as c
from fastui.events import BackEvent, GoToEvent


def get_common_content(
    *components: AnyComponent,
    title: str | None = None,
) -> list[AnyComponent]:
    return [
        c.PageTitle(text=f"English buddy — {title}" if title else "admin panel"),
        c.Navbar(
            start_links=[
                c.Link(
                    components=[c.Text(text='Уроки')],
                    on_click=GoToEvent(url='/lessons'),
                ),
                c.Link(
                    components=[c.Text(text='Тексты')],
                    on_click=GoToEvent(url='/texts'),
                ),
                c.Link(
                    components=[c.Text(text='Реакции')],
                    on_click=GoToEvent(url='/reactions'),
                ),
                c.Link(
                    components=[c.Text(text='Рассылка')],
                    on_click=GoToEvent(url='/newsletter'),
                ),
                c.Link(
                    components=[c.Text(text='Пользователи')],
                    on_click=GoToEvent(url='/users'),
                ),
                c.Link(
                    components=[c.Text(text='Статистика')],
                    on_click=GoToEvent(url='/statistics'),
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
        #     links=[
        #         c.Link(
        #             components=[c.Text(text='можно вот тут ссылку на мониторинг сделать')],
        #             on_click=GoToEvent(url='...'),
        #         ),
        #     ],
        # ),
    ]


back_button = c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent())
