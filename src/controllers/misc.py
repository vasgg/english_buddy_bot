import enum
from enum import Enum
import mimetypes
from pathlib import Path
from typing import Type

from fastui import components as c
from fastui.events import GoToEvent

from bot.resources.enums import NavigationObjectType, SlideType
from config import Settings
from database.models.slide import Slide


def get_pictures_list_from_directory(lesson_id: int) -> Type[Enum]:
    files = {}
    directory = Path(f"src/webapp/static/images/lesson_{lesson_id}")
    for file in directory.iterdir():
        if file.is_file():
            mime_type, _ = mimetypes.guess_type(file)
            if mime_type in Settings.allowed_file_types_to_upload:
                file_name = file.stem.replace("-", "_").replace(" ", "_")
                files[file_name.upper()] = file_name
    enum_class = enum.Enum('FilesEnum', files)
    return enum_class


def get_nav_keyboard(mode: NavigationObjectType, prev_obj_id: int | None, next_obj_id: int | None) -> list:
    buttons = []
    url_further = (
        f'/{mode.value}/edit/{next_obj_id}/' if next_obj_id is not None else f'/{mode.value}/{prev_obj_id + 1}/'
    )
    url_back = f'/{mode.value}/edit/{prev_obj_id}/' if prev_obj_id is not None else f'/{mode.value}/{next_obj_id - 1}/'
    buttons.append(
        c.Link(
            components=[c.Button(text='◀︎', named_style='secondary', class_name='+ ms-2')],
            on_click=GoToEvent(url=url_back),
            # on_click=GoToEvent(url=url_back),
        )
    )
    buttons.append(
        c.Link(
            components=[c.Button(text='►', named_style='secondary', class_name='+ ms-2')],
            on_click=GoToEvent(url=url_further),
        )
    )
    return buttons


def get_slide_emoji(slide_type: SlideType) -> str:
    slide_type_to_emoji = {
        'text': '🖋',
        'image': '🖼',
        'pin_dict': '📎',
        'small_sticker': '🧨',
        'big_sticker': '💣',
        'quiz_options': '🧩',
        'quiz_input_word': '🗨',
        'quiz_input_phrase': '💬',
        'final_slide': '🎉',
    }
    return slide_type_to_emoji.get(slide_type.value, '')


def get_slide_details(slide: Slide) -> str:
    slide_type_to_str = {
        'text': slide.keyboard_type if slide.keyboard_type else ' ',
        'image': ' ',
        'pin_dict': ' ',
        'small_sticker': ' ',
        'big_sticker': ' ',
        'quiz_options': slide.keyboard,
        'quiz_input_word': slide.right_answers,
        'quiz_input_phrase': slide.right_answers,
        'final_slide': ' ',
    }
    return slide_type_to_str.get(slide.slide_type.value, ' ')
