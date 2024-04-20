import logging

from fastui import components as c

from database.crud.lesson import get_lesson_by_id
from database.crud.slide import get_slide_by_id
from database.models.lesson import Lesson
from database.models.slide import Slide
from enums import MoveSlideDirection, PathType, SlideType, SlidesMenuType, StickerType
from lesson_path import LessonPath
from webapp.controllers.misc import get_slide_details, get_slide_emoji
from webapp.db import AsyncDBSession
from webapp.schemas.slide import (
    SlidesTableSchema,
    get_image_slide_data_model,
    get_pin_dict_slide_data_model,
    get_quiz_input_phrase_slide_data_model,
    get_quiz_input_word_slide_data_model,
    get_quiz_options_slide_data_model,
    get_text_slide_data_model,
)

logger = logging.getLogger()


async def get_all_slides_from_lesson_by_order_fastui(db_session: AsyncDBSession, path: str | None = None) -> list:
    lesson_path = LessonPath(path).path
    ordered_slides = []
    for index, slide_id in enumerate(lesson_path, start=1):
        slide = await get_slide_by_id(slide_id, db_session)
        slide_text = (
            slide.slide_type.value.replace('_', ' ').capitalize() if 'sticker' in slide.slide_type.value else slide.text
        )
        slide_data = {
            'id': slide.id,
            'lesson_id': slide.lesson_id,
            'slide_type': slide.slide_type,
            'index': index,
            'emoji': get_slide_emoji(slide.slide_type),
            'text': slide.picture if slide.slide_type.value == 'image' else slide_text,
            'details': get_slide_details(slide),
            'is_exam_slide': '🎓' if slide.is_exam_slide else ' ',
            'edit_button': '✏️',
            'up_button': '🔼',
            'down_button': '🔽',
            'plus_button': '➕',
            'minus_button': '➖',
        }
        validated_slide = SlidesTableSchema.model_validate(slide_data)
        ordered_slides.append(validated_slide)
    logger.info(f"Processed slides: {len(ordered_slides)}")
    return ordered_slides


async def create_new_sticker(
    lesson_id: int,
    sticker_type: StickerType,
    db_session: AsyncDBSession,
) -> int:
    new_slide: Slide = Slide(
        slide_type=SlideType.SMALL_STICKER if sticker_type == StickerType.SMALL else SlideType.BIG_STICKER,
        lesson_id=lesson_id,
    )
    db_session.add(new_slide)
    await db_session.flush()
    return new_slide.id


def get_new_slide_form_by_slide_type(
    slide_type: SlideType,
    lesson_id: int,
    source: SlidesMenuType,
    index: int | None = None,
) -> c.ModelForm:
    suffix = f'?index={index}' if index is not None else ''
    match slide_type:
        case SlideType.TEXT:
            submit_url = f'/api/slides/new/{lesson_id}/{source}/text/' + suffix
            form = c.ModelForm(model=get_text_slide_data_model(), submit_url=submit_url)
        case SlideType.IMAGE:
            submit_url = f'/api/slides/new/{lesson_id}/{source}/image/' + suffix
            form = c.ModelForm(model=get_image_slide_data_model(lesson_id=lesson_id), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/slides/new/{lesson_id}/{source}/dict/' + suffix
            form = c.ModelForm(model=get_pin_dict_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/slides/new/{lesson_id}/{source}/quiz_options/' + suffix
            form = c.ModelForm(model=get_quiz_options_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/slides/new/{lesson_id}/{source}/quiz_input_word/' + suffix
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/slides/new/{lesson_id}/{source}/quiz_input_phrase/' + suffix
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(), submit_url=submit_url)
        case _:
            raise AssertionError(f'Unexpected slide type: {slide_type}')
    return form


def get_edit_slide_form_by_slide_type(
    source: SlidesMenuType,
    slide: Slide,
    index: int,
) -> c.ModelForm:
    match slide.slide_type:
        case SlideType.TEXT:
            submit_url = f'/api/slides/edit/{source}/text/{slide.id}/{index}/'
            form = c.ModelForm(model=get_text_slide_data_model(slide), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/slides/edit/{source}/dict/{slide.id}/{index}/'
            form = c.ModelForm(model=get_pin_dict_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/slides/edit/{source}/quiz_options/{slide.id}/{index}/'
            form = c.ModelForm(model=get_quiz_options_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/slides/edit/{source}/quiz_input_word/{slide.id}/{index}/'
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/slides/edit/{source}/quiz_input_phrase/{slide.id}/{index}/'
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(slide), submit_url=submit_url)
        case _:
            raise AssertionError(f'Unexpected slide type: {slide.slide_type}')
    return form


def delete_slide(
    lesson: Lesson,
    source: SlidesMenuType,
    index: int,
):
    match source:
        case SlidesMenuType.REGULAR:
            lesson_path = LessonPath(lesson.path)
            lesson_path.remove_slide(index)
            lesson.path = str(lesson_path)
        case SlidesMenuType.EXTRA:
            lesson_path = LessonPath(lesson.path_extra)
            lesson_path.remove_slide(index)
            lesson.path_extra = str(lesson_path)
        case _:
            raise AssertionError(f'Unexpected source: {source}')


def move_slide(
    lesson: Lesson,
    source: SlidesMenuType,
    mode: MoveSlideDirection,
    index: int,
):
    match source:
        case SlidesMenuType.REGULAR:
            lesson_path = LessonPath(lesson.path)
            lesson_path.move_slide(mode, index)
            lesson.path = str(lesson_path)
        case SlidesMenuType.EXTRA:
            lesson_path = LessonPath(lesson.path_extra)
            lesson_path.move_slide(mode, index)
            lesson.path_extra = str(lesson_path)
        case _:
            raise AssertionError(f'Unexpected source: {source}')


async def update_lesson_path(
    lesson_id: int,
    source: SlidesMenuType,
    slide_id: int,
    db_session: AsyncDBSession,
    index: int | None = None,
    mode: PathType | None = None,
) -> None:
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    match source:
        case SlidesMenuType.REGULAR:
            if index is None:
                lesson.path = str(slide_id)
            else:
                lesson.path = compose_lesson_path(index, lesson.path, mode, slide_id)
        case SlidesMenuType.EXTRA:
            if index is None:
                lesson.path_extra = str(slide_id)
            else:
                lesson.path_extra = compose_lesson_path(index, lesson.path_extra, mode, slide_id)
        case _:
            raise AssertionError(f'Unexpected source: {source}')


def compose_lesson_path(index, path, mode, slide_id) -> str:
    lesson_path = LessonPath(path)
    match mode:
        case PathType.EXISTING_PATH_NEW:
            lesson_path.add_slide(index, slide_id)
        case PathType.EXISTING_PATH_EDIT:
            lesson_path.edit_slide(index, slide_id)
    return str(lesson_path)
