import logging

from fastui import components as c

from database.crud.media_asset import get_media_assets_by_ids
from database.crud.slide import get_slides_by_ids
from database.models.lesson import Lesson
from database.models.slide import Slide
from enums import MoveSlideDirection, SlideType, SlidesMenuType, StickerType
from lesson_path import LessonPath
from webapp.controllers.misc import get_slide_details, get_slide_emoji
from webapp.db import AsyncDBSession
from webapp.schemas.slide import (
    SlidesTableSchema,
    get_image_slide_data_model,
    get_media_slide_data_model,
    get_pin_dict_slide_data_model,
    get_quiz_input_phrase_slide_data_model,
    get_quiz_input_word_slide_data_model,
    get_quiz_options_slide_data_model,
    get_text_slide_data_model,
)

logger = logging.getLogger()


async def get_all_slides_from_lesson_by_order_fastui(
    db_session: AsyncDBSession,
    lesson_id: int,
    path: str | None = None,
) -> list:
    lesson_path = LessonPath(path).path
    slides_by_id = await get_slides_by_ids(lesson_path, db_session)
    media_asset_ids = [
        slide.media_asset_id
        for slide in slides_by_id.values()
        if slide.slide_type == SlideType.MEDIA and slide.media_asset_id is not None
    ]
    media_assets_by_id = await get_media_assets_by_ids(media_asset_ids, db_session)
    ordered_slides = []
    for index, slide_id in enumerate(lesson_path, start=1):
        slide = slides_by_id.get(slide_id)
        if slide is None:
            logger.warning("Slide not found in DB (lesson_id=%s, index=%s, slide_id=%s)", lesson_id, index, slide_id)
            slide_data = {
                "id": str(slide_id),
                "lesson_id": lesson_id,
                "slide_type": SlideType.TEXT,
                "index": index,
                "emoji": "⚠️",
                "text": "⚠️ Слайд не найден в БД — удалите или замените его в lesson.path",
                "delay": " ",
                "details": " ",
                "is_exam_slide": " ",
                "edit_button": " ",
                "up_button": "🔼",
                "down_button": "🔽",
                "plus_button": "➕",
                "minus_button": "➖",
            }
        else:
            if slide.slide_type == SlideType.MEDIA:
                media_asset = media_assets_by_id.get(slide.media_asset_id) if slide.media_asset_id else None
                if media_asset is None:
                    slide_text = "⚠️ Медиа не найдено в БД"
                    details = "⚠️"
                else:
                    slide_text = media_asset.comment or media_asset.file_name or media_asset.file_id
                    details = media_asset.media_type
            else:
                slide_text = (
                    slide.slide_type.value.replace("_", " ").capitalize()
                    if "sticker" in slide.slide_type.value
                    else slide.text
                )
                details = get_slide_details(slide)

            slide_text = slide.picture if slide.slide_type.value == "image" else slide_text
            # noinspection PyTypeChecker
            slide_data = {
                "id": str(slide.id),
                "lesson_id": lesson_id,
                "slide_type": slide.slide_type,
                "index": index,
                "emoji": get_slide_emoji(slide.slide_type),
                "text": slide_text,
                "delay": str(int(slide.delay)) if slide.delay else " ",
                "details": details,
                "is_exam_slide": "🎓" if slide.is_exam_slide else " ",
                "edit_button": "✏️",
                "up_button": "🔼",
                "down_button": "🔽",
                "plus_button": "➕",
                "minus_button": "➖",
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
    suffix = f"?index={index}" if index is not None else ""
    match slide_type:
        case SlideType.TEXT:
            submit_url = f"/api/slides/new/{lesson_id}/{source}/text/" + suffix
            form = c.ModelForm(model=get_text_slide_data_model(), submit_url=submit_url)
        case SlideType.IMAGE:
            submit_url = f"/api/slides/new/{lesson_id}/{source}/image/" + suffix
            form = c.ModelForm(model=get_image_slide_data_model(lesson_id=lesson_id), submit_url=submit_url)
        case SlideType.MEDIA:
            submit_url = f"/api/slides/new/{lesson_id}/{source}/media/" + suffix
            form = c.ModelForm(model=get_media_slide_data_model(), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f"/api/slides/new/{lesson_id}/{source}/dict/" + suffix
            form = c.ModelForm(model=get_pin_dict_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f"/api/slides/new/{lesson_id}/{source}/quiz_options/" + suffix
            form = c.ModelForm(model=get_quiz_options_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f"/api/slides/new/{lesson_id}/{source}/quiz_input_word/" + suffix
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f"/api/slides/new/{lesson_id}/{source}/quiz_input_phrase/" + suffix
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(), submit_url=submit_url)
        case _:
            raise AssertionError(f"Unexpected slide type: {slide_type}")
    return form


def get_edit_slide_form_by_slide_type(
    source: SlidesMenuType,
    slide: Slide,
    index: int,
    media_file_id: str | None = None,
    media_type: str | None = None,
    media_comment: str | None = None,
) -> c.ModelForm:
    match slide.slide_type:
        case SlideType.TEXT:
            submit_url = f"/api/slides/edit/{source}/text/{slide.id}/{index}/"
            form = c.ModelForm(model=get_text_slide_data_model(slide), submit_url=submit_url)
        case SlideType.MEDIA:
            submit_url = f"/api/slides/edit/{source}/media/{slide.id}/{index}/"
            form = c.ModelForm(
                model=get_media_slide_data_model(
                    slide,
                    media_file_id=media_file_id,
                    media_type=media_type,
                    media_comment=media_comment,
                ),
                submit_url=submit_url,
            )
        case SlideType.PIN_DICT:
            submit_url = f"/api/slides/edit/{source}/dict/{slide.id}/{index}/"
            form = c.ModelForm(model=get_pin_dict_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f"/api/slides/edit/{source}/quiz_options/{slide.id}/{index}/"
            form = c.ModelForm(model=get_quiz_options_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f"/api/slides/edit/{source}/quiz_input_word/{slide.id}/{index}/"
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f"/api/slides/edit/{source}/quiz_input_phrase/{slide.id}/{index}/"
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(slide), submit_url=submit_url)
        case _:
            raise AssertionError(f"Unexpected slide type: {slide.slide_type}")
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
            raise AssertionError(f"Unexpected source: {source}")


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
            raise AssertionError(f"Unexpected source: {source}")
