from fastui import components as c
from fastui.events import BackEvent, GoToEvent

from enums import SlidesMenuType

back_button = c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent())
create_lesson_button = c.Button(text='Создать урок', on_click=GoToEvent(url='/lessons/add_lesson/'))


def create_new_slide_button_by_mode(lesson_id: int, mode: SlidesMenuType):
    text = 'Создать слайд' if mode == SlidesMenuType.REGULAR else 'Создать экстра слайд'
    return c.Button(text=text, on_click=GoToEvent(url=f'/slides/plus_button/{mode}/{lesson_id}/'))
