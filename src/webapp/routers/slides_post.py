import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastui import FastUI
from fastui import components as c
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from config import Settings, get_settings
from database.crud.media_asset import get_media_asset_by_file_id
from database.crud.slide import get_slide_by_id
from database.models.slide import Slide
from enums import KeyboardType, PathType, SlideType, SlidesMenuType, StickerType
from webapp.controllers.lesson import update_lesson_path
from webapp.controllers.misc import extract_img_from_form, image_upload
from webapp.routers.components.buttons import back_button
from webapp.routers.components.components import get_common_content
from webapp.db import AsyncDBSession
from webapp.schemas.slide import (
    EditDictSlideData,
    EditImageSlideData,
    EditMediaSlideData,
    EditQuizInputPhraseSlideData,
    EditQuizInputWordSlideData,
    EditQuizOptionsSlideData,
    EditTextSlideDataModel,
    get_media_slide_data_model,
)
from webapp.schemas.sticker import EditStickerSlideDataModel

router = APIRouter()
logger = logging.getLogger()


def _render_media_not_found_form(
    *,
    title: str,
    submit_url: str,
    form: EditMediaSlideData,
) -> list:
    return get_common_content(
        back_button,
        c.Paragraph(text=""),
        c.Paragraph(
            text=(
                f"❌ Медиа с file_id {form.media_id} не найдено. "
                "Чтобы добавить его, отправьте этот файл в чат MEDIA_CHAT_ID и повторите попытку."
            )
        ),
        c.Paragraph(text=""),
        c.ModelForm(
            model=get_media_slide_data_model(media_file_id=form.media_id),
            submit_url=submit_url,
            initial=form.model_dump(),
        ),
        title=title,
    )


@router.post("/edit/{source}/text/{slide_id}/{index}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_text_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditTextSlideDataModel, fastui_form(EditTextSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    new_slide: Slide = Slide(
        slide_type=SlideType.TEXT,
        lesson_id=slide.lesson_id,
        text=form.text,
        delay=form.delay,
        is_exam_slide=form.is_exam_slide,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post("/edit/{source}/dict/{slide_id}/{index}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_dict_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditDictSlideData, fastui_form(EditDictSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    new_slide: Slide = Slide(
        slide_type=SlideType.PIN_DICT,
        lesson_id=slide.lesson_id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post("/edit/{source}/sticker/{slide_id}/{index}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_sticker_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditStickerSlideDataModel, fastui_form(EditStickerSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide_type = SlideType.BIG_STICKER if form.sticker_type == StickerType.BIG else SlideType.SMALL_STICKER
    new_slide: Slide = Slide(
        slide_type=slide_type,
        lesson_id=slide.lesson_id,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post(
    "/edit/{source}/quiz_options/{slide_id}/{index}/", response_model=FastUI, response_model_exclude_none=True
)
async def edit_quiz_option_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizOptionsSlideData, fastui_form(EditQuizOptionsSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_OPTIONS,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        keyboard_type=KeyboardType.QUIZ,
        keyboard=form.keyboard,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post(
    "/edit/{source}/quiz_input_word/{slide_id}/{index}/",
    response_model=FastUI,
    response_model_exclude_none=True,
)
async def edit_quiz_input_word_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputWordSlideData, fastui_form(EditQuizInputWordSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_WORD,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        almost_right_answers=form.almost_right_answers,
        almost_right_answer_reply=form.almost_right_answer_reply,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post(
    "/edit/{source}/quiz_input_phrase/{slide_id}/{index}/", response_model=FastUI, response_model_exclude_none=True
)
async def edit_quiz_input_phrase_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputPhraseSlideData, fastui_form(EditQuizInputPhraseSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_PHRASE,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        almost_right_answers=form.almost_right_answers,
        almost_right_answer_reply=form.almost_right_answer_reply,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post("/edit/{source}/image/{slide_id}/{index}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_image_slide(
    image_file: Annotated[bytes, Depends(extract_img_from_form)],
    settings: Annotated[Settings, Depends(get_settings)],
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditImageSlideData, fastui_form(EditImageSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    if form.upload_new_picture.filename != "":
        image_upload(image_file, form, slide.lesson_id, settings)
        slide.picture = form.upload_new_picture.filename
    else:
        slide_picture = form.select_picture if form.select_picture else slide.picture
        new_slide: Slide = Slide(
            slide_type=SlideType.IMAGE,
            lesson_id=slide.lesson_id,
            picture=slide_picture,
            delay=form.delay,
            keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
        )
        db_session.add(new_slide)
        await db_session.flush()
        await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post("/edit/{source}/media/{slide_id}/{index}/", response_model=FastUI, response_model_exclude_none=True)
async def edit_media_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditMediaSlideData, fastui_form(EditMediaSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    media_asset = await get_media_asset_by_file_id(form.media_id, db_session)
    submit_url = f"/api/slides/edit/{source}/media/{slide_id}/{index}/"
    if media_asset is None:
        return _render_media_not_found_form(
            title=f"Редактирование слайда {slide_id} | media",
            submit_url=submit_url,
            form=form,
        )

    new_slide: Slide = Slide(
        slide_type=SlideType.MEDIA,
        lesson_id=slide.lesson_id,
        media_asset_id=media_asset.id,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(slide.lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_EDIT)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{slide.lesson_id}/"))]


@router.post("/new/{lesson_id}/{source}/text/", response_model=FastUI, response_model_exclude_none=True)
async def new_text_slide_form(
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
    form: Annotated[EditTextSlideDataModel, fastui_form(EditTextSlideDataModel)],
    index: int | None = None,
):
    new_slide: Slide = Slide(
        slide_type=SlideType.TEXT,
        lesson_id=lesson_id,
        text=form.text,
        delay=form.delay,
        is_exam_slide=form.is_exam_slide,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_NEW)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{lesson_id}/"))]


@router.post("/new/{lesson_id}/{source}/image/", response_model=FastUI, response_model_exclude_none=True)
async def new_image_slide_form(
    image_file: Annotated[bytes, Depends(extract_img_from_form)],
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
    form: Annotated[EditImageSlideData, fastui_form(EditImageSlideData)],
    settings: Annotated[Settings, Depends(get_settings)],
    index: int | None = None,
):
    slide_picture = None
    if form.upload_new_picture.filename != "":
        image_upload(image_file, form, lesson_id, settings)
        slide_picture = form.upload_new_picture.filename
    elif form.select_picture:
        slide_picture = form.select_picture
    new_slide: Slide = Slide(
        slide_type=SlideType.IMAGE,
        lesson_id=lesson_id,
        picture=slide_picture,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_NEW)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{lesson_id}/"))]


@router.post("/new/{lesson_id}/{source}/media/", response_model=FastUI, response_model_exclude_none=True)
async def new_media_slide_form(
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
    form: Annotated[EditMediaSlideData, fastui_form(EditMediaSlideData)],
    index: int | None = None,
):
    media_asset = await get_media_asset_by_file_id(form.media_id, db_session)
    suffix = f"?index={index}" if index is not None else ""
    submit_url = f"/api/slides/new/{lesson_id}/{source}/media/{suffix}"
    if media_asset is None:
        return _render_media_not_found_form(
            title="Создание слайда | media",
            submit_url=submit_url,
            form=form,
        )

    new_slide: Slide = Slide(
        slide_type=SlideType.MEDIA,
        lesson_id=lesson_id,
        media_asset_id=media_asset.id,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_NEW)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{lesson_id}/"))]


@router.post("/new/{lesson_id}/{source}/dict/", response_model=FastUI, response_model_exclude_none=True)
async def new_dict_slide(
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
    form: Annotated[EditDictSlideData, fastui_form(EditDictSlideData)],
    index: int | None = None,
):
    new_slide: Slide = Slide(
        slide_type=SlideType.PIN_DICT,
        lesson_id=lesson_id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_NEW)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{lesson_id}/"))]


@router.post("/new/{lesson_id}/{source}/quiz_options/", response_model=FastUI, response_model_exclude_none=True)
async def new_quiz_option_slide(
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizOptionsSlideData, fastui_form(EditQuizOptionsSlideData)],
    index: int | None = None,
):
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_OPTIONS,
        lesson_id=lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        keyboard=form.keyboard,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_NEW)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{lesson_id}/"))]


@router.post("/new/{lesson_id}/{source}/quiz_input_word/", response_model=FastUI, response_model_exclude_none=True)
async def new_quiz_input_word_slide(
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputWordSlideData, fastui_form(EditQuizInputWordSlideData)],
    index: int | None = None,
):
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_WORD,
        lesson_id=lesson_id,
        text=form.text,
        almost_right_answers=form.almost_right_answers,
        almost_right_answer_reply=form.almost_right_answer_reply,
        right_answers=form.right_answers,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_NEW)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{lesson_id}/"))]


@router.post("/new/{lesson_id}/{source}/quiz_input_phrase/", response_model=FastUI, response_model_exclude_none=True)
async def new_quiz_input_phrase_slide(
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputPhraseSlideData, fastui_form(EditQuizInputPhraseSlideData)],
    index: int | None = None,
):
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_PHRASE,
        lesson_id=lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        almost_right_answers=form.almost_right_answers,
        almost_right_answer_reply=form.almost_right_answer_reply,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    await update_lesson_path(lesson_id, source, new_slide.id, db_session, index, PathType.EXISTING_PATH_NEW)
    return [c.FireEvent(event=GoToEvent(url=f"/slides/lesson{lesson_id}/"))]
