from fastui import AnyComponent
from fastui import components as c
from fastui.events import BackEvent, GoToEvent

from enums import SlidesMenuType

c.AnyComponent = AnyComponent  # type: ignore[attr-defined]
c.Link.model_rebuild()

back_button = c.Link(components=[c.Button(text="Назад", named_style="secondary")], on_click=BackEvent())
create_lesson_button = c.Button(text="Создать урок", on_click=GoToEvent(url="/lessons/add_lesson/"))


def create_new_slide_button_by_mode(lesson_id: int, mode: SlidesMenuType):
    text = "Создать слайд" if mode == SlidesMenuType.REGULAR else "Создать экстра слайд"
    return c.Button(text=text, on_click=GoToEvent(url=f"/slides/plus_button/{mode}/{lesson_id}/"))


def create_send_message_button(user_id: int) -> AnyComponent:
    return c.Link(
        components=[c.Button(text="Отправить сообщение", named_style="warning")],
        on_click=GoToEvent(url=f"/users/send_message/{user_id}/"),
    )
