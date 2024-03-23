import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent
from fastui.forms import fastui_form

from config import Settings, get_settings
from database.crud.lesson import get_lesson_by_id
from database.crud.slide import get_slide_by_id
from database.models.lesson import Lesson
from database.models.slide import Slide
from enums import KeyboardType, SlideType, SlidesMenuType, StickerType
from webapp.controllers.misc import extract_img_from_form
from webapp.controllers.slide import (
    get_all_slides_from_lesson_by_order_fastui,
)
from webapp.db import AsyncDBSession
from webapp.routers.components.main_component import get_common_content
from webapp.schemas.slide import (
    EditDictSlideData,
    EditImageSlideData,
    EditQuizInputPhraseSlideData,
    EditQuizInputWordSlideData,
    EditQuizOptionsSlideData,
    EditTextSlideDataModel,
    get_image_slide_data_model,
    get_pin_dict_slide_data_model,
    get_quiz_input_phrase_slide_data_model,
    get_quiz_input_word_slide_data_model,
    get_quiz_options_slide_data_model,
    get_text_slide_data_model,
)
from webapp.schemas.sticker import EditStickerSlideDataModel, get_sticker_slide_data_model

router = APIRouter()
logger = logging.getLogger()
default_errors_threshold = 50


@router.get("/lesson{lesson_id}/", response_model=FastUI, response_model_exclude_none=True)
async def slides_page(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    slides = await get_all_slides_from_lesson_by_order_fastui(lesson.path, db_session)
    extra_slides_table = None
    if lesson.path_extra:
        extra_slides = await get_all_slides_from_lesson_by_order_fastui(str(lesson.path_extra), db_session)
        extra_slides_table = c.Table(
            data=extra_slides,
            columns=[
                DisplayLookup(field='index', table_width_percent=3),
                DisplayLookup(field='emoji', table_width_percent=3),
                DisplayLookup(field='text'),
                DisplayLookup(field='details', table_width_percent=23),
                DisplayLookup(
                    field='edit_button',
                    on_click=GoToEvent(url='/slides/edit/extra/{index}/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='up_button',
                    on_click=GoToEvent(url='/slides/up_button/extra/{index}/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='down_button',
                    on_click=GoToEvent(url='/slides/down_button/extra/{index}/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='plus_button',
                    on_click=GoToEvent(url='/slides/plus_button/extra/{index}/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='minus_button',
                    on_click=GoToEvent(url='/slides/confirm_delete/extra/{index}/{id}/'),
                    table_width_percent=3,
                ),
            ],
        )
    if len(slides) == 0:
        return get_common_content(
            c.Paragraph(text=''),
            c.Paragraph(text='В этом уроке ещё нет слайдов.'),
            c.Button(text='Назад', named_style='secondary', on_click=BackEvent()),
            c.Paragraph(text=''),
            c.Button(text='Создать слайд', on_click=GoToEvent(url=f'/slides/plus_button/regular/0/{lesson.id}/')),
            title=f'Слайды | Урок {lesson.index} | {lesson.title}',
        )

    slides_table = c.Table(
        data=slides,
        columns=[
            DisplayLookup(field='index', table_width_percent=3),
            DisplayLookup(field='emoji', table_width_percent=3),
            DisplayLookup(field='text'),
            DisplayLookup(field='details', table_width_percent=20),
            DisplayLookup(field='is_exam_slide', table_width_percent=3),
            DisplayLookup(
                field='edit_button',
                on_click=GoToEvent(url='/slides/edit/regular/{index}/{id}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='up_button',
                on_click=GoToEvent(url='/slides/up_button/regular/{index}/{id}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='down_button',
                on_click=GoToEvent(url='/slides/down_button/regular/{index}/{id}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='plus_button',
                on_click=GoToEvent(url='/slides/plus_button/regular/{index}/{id}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/slides/confirm_delete/regular/{index}/{id}/'),
                table_width_percent=3,
            ),
        ],
    )
    if not lesson.path_extra:
        return get_common_content(
            c.Paragraph(text=''),
            slides_table,
            c.Paragraph(text=''),
            c.Paragraph(text='В этом уроке нет экстра слайдов.'),
            c.Paragraph(text=''),
            c.Button(text='Создать экстра слайд', on_click=GoToEvent(url=f'/slides/plus_button/extra/0/{lesson.id}/')),
            c.Paragraph(text=''),
            title=f'Слайды | Урок {lesson.index} | {lesson.title}',
        )

    return get_common_content(
        c.Paragraph(text=''),
        slides_table,
        c.Paragraph(text=''),
        c.Heading(text='Экстра слайды', level=3),
        c.Paragraph(text=''),
        extra_slides_table if lesson.path_extra else c.Paragraph(text=''),
        title=f'Слайды | Урок {lesson.index} | {lesson.title}',
    )


@router.get('/edit/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_slide(
    index: int, slide_id: int, source: SlidesMenuType, db_session: AsyncDBSession
) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    optionnal_component = c.Paragraph(text='')
    match slide.slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            submit_url = f'/api/slides/edit/sticker/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_sticker_slide_data_model(slide), submit_url=submit_url)
        case SlideType.TEXT:
            submit_url = f'/api/slides/edit/text/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_text_slide_data_model(slide), submit_url=submit_url)
        case SlideType.IMAGE:
            optionnal_component = c.Div(
                components=[
                    c.Image(
                        src=f'/static/lessons_images/{slide.lesson_id}/{slide.picture}',
                        width=600,
                        # height=200,
                        loading='lazy',
                        referrer_policy='no-referrer',
                        # class_name='border rounded',
                    ),
                    c.Paragraph(text=''),
                ]
            )
            submit_url = f'/api/slides/edit/image/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_image_slide_data_model(slide), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/slides/edit/dict/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_pin_dict_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/slides/edit/quiz_option/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_options_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/slides/edit/quiz_input_word/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/slides/edit/quiz_input_phrase/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(slide), submit_url=submit_url)
        case _:
            raise HTTPException(status_code=404, detail="Unexpected slide type")
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=''),
        optionnal_component,
        c.Paragraph(text=''),
        form,
        title=f'edit | slide {slide_id} | {slide.slide_type.value}',
    )


@router.post('/edit/sticker/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_sticker_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditStickerSlideDataModel, fastui_form(EditStickerSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )

    if form.sticker_type == StickerType.BIG:
        slide_type = SlideType.BIG_STICKER
    else:
        slide_type = SlideType.SMALL_STICKER
    new_slide: Slide = Slide(
        slide_type=slide_type,
        lesson_id=slide.lesson_id,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index - 1] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    if source == SlidesMenuType.REGULAR:
        lesson.path = path
    else:
        lesson.path_extra = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.post('/edit/text/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_text_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditTextSlideDataModel, fastui_form(EditTextSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
    new_slide: Slide = Slide(
        slide_type=SlideType.TEXT,
        lesson_id=slide.lesson_id,
        text=form.text,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index - 1] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    if source == SlidesMenuType.REGULAR:
        lesson.path = path
    else:
        lesson.path_extra = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.post('/edit/dict/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_dict_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditDictSlideData, fastui_form(EditDictSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
    new_slide: Slide = Slide(
        slide_type=SlideType.PIN_DICT,
        lesson_id=slide.lesson_id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    if source == SlidesMenuType.REGULAR:
        lesson.path = path
    else:
        lesson.path_extra = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.post('/edit/quiz_option/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_option_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizOptionsSlideData, fastui_form(EditQuizOptionsSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
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
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    if source == SlidesMenuType.REGULAR:
        lesson.path = path
    else:
        lesson.path_extra = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.post(
    '/edit/quiz_input_word/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True
)
async def edit_quiz_input_word_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputWordSlideData, fastui_form(EditQuizInputWordSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_WORD,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    if source == SlidesMenuType.REGULAR:
        lesson.path = path
    else:
        lesson.path_extra = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.post(
    '/edit/quiz_input_phrase/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True
)
async def edit_quiz_input_phrase_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputPhraseSlideData, fastui_form(EditQuizInputPhraseSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
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
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    if source == SlidesMenuType.REGULAR:
        lesson.path = path
    else:
        lesson.path_extra = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.post('/edit/image/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
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
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
    if form.upload_new_picture.filename != '':
        image_upload(image_file, form, lesson.id, settings)
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
        slides_ids[index] = new_slide.id
        path = '.'.join([str(slideid) for slideid in slides_ids])
        if source == SlidesMenuType.REGULAR:
            lesson.path = path
        else:
            lesson.path_extra = path
        await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.get('/new/{slide_type}/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def create_slide(
    source: SlidesMenuType,
    slide_type: SlideType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    match slide_type:
        case SlideType.TEXT:
            submit_url = f'/api/slides/new/text/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_text_slide_data_model(), submit_url=submit_url)
        case SlideType.IMAGE:
            submit_url = f'/api/slides/new/image/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_image_slide_data_model(lesson_id=slide.lesson_id), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/slides/new/dict/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_pin_dict_slide_data_model(), submit_url=submit_url)
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            if source == SlidesMenuType.EXTRA:
                if index == 0:
                    lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
                new_slide: Slide = Slide(
                    slide_type=SlideType.SMALL_STICKER
                    if slide_type == SlideType.SMALL_STICKER
                    else SlideType.BIG_STICKER,
                    lesson_id=lesson.id,
                )
                db_session.add(new_slide)
                await db_session.flush()
                if index == 0:
                    path = str(new_slide.id)
                    lesson.path_extra = path
                else:
                    slides_ids = [int(slideid) for slideid in lesson.path_extra.split('.')]
                    slides_ids.insert(index, new_slide.id)
                    path = '.'.join([str(slideid) for slideid in slides_ids])
                    lesson.path_extra = path
                lesson.errors_threshold = default_errors_threshold
                await db_session.commit()
                return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
            if index == 0:
                lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
            new_slide: Slide = Slide(
                slide_type=SlideType.SMALL_STICKER if slide_type == SlideType.SMALL_STICKER else SlideType.BIG_STICKER,
                lesson_id=lesson.id,
            )
            db_session.add(new_slide)
            await db_session.flush()
            if index == 0:
                path = str(new_slide.id)
                lesson.path = path
            else:
                slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
                slides_ids.insert(index, new_slide.id)
                path = '.'.join([str(slideid) for slideid in slides_ids])
                lesson.path = path
            lesson.errors_threshold = default_errors_threshold
            await db_session.commit()
            return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/slides/new/quiz_option/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_options_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/slides/new/quiz_input_word/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/slides/new/quiz_input_phrase/{source}/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(), submit_url=submit_url)
        case _:
            assert False, 'Unexpected slide type'
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=f''),
        form,
        title=f'Создание слайда | {slide_type.value}',
    )


@router.post('/new/text/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_text_slide_form(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditTextSlideDataModel, fastui_form(EditTextSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    if source == SlidesMenuType.EXTRA:
        if index == 0:
            lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.TEXT,
            lesson_id=lesson.id,
            text=form.text,
            delay=form.delay,
            keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
        )
        db_session.add(new_slide)
        await db_session.flush()
        if index == 0:
            path = str(new_slide.id)
            lesson.path_extra = path
        else:
            slides_ids = [int(slideid) for slideid in lesson.path_extra.split('.')]
            slides_ids.insert(index, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path_extra = path
        lesson.errors_threshold = default_errors_threshold
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    if index == 0:
        lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.TEXT,
            lesson_id=lesson.id,
            text=form.text,
            delay=form.delay,
            keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
        )
        db_session.add(new_slide)
        await db_session.flush()
        path = str(new_slide.id)
        lesson.path = path
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
    new_slide: Slide = Slide(
        slide_type=SlideType.TEXT,
        lesson_id=lesson.id,
        text=form.text,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]


@router.post('/new/image/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_image_slide_form(
    image_file: Annotated[bytes, Depends(extract_img_from_form)],
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditImageSlideData, fastui_form(EditImageSlideData)],
    settings: Annotated[Settings, Depends(get_settings)],

):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slide_picture = form.select_picture if form.select_picture else form.upload_new_picture.filename
    if form.upload_new_picture.filename != '':
        image_upload(image_file, form, lesson.id, settings)
        slide.picture = form.upload_new_picture.filename
    else:
        slide_picture = form.select_picture if form.select_picture else slide.picture
    if source == SlidesMenuType.EXTRA:
        if index == 0:
            lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.IMAGE,
            lesson_id=lesson.id,
            picture=slide_picture,
            delay=form.delay,
            keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
        )
        db_session.add(new_slide)
        await db_session.flush()
        if index == 0:
            path = str(new_slide.id)
            lesson.path_extra = path
        else:
            slides_ids = [int(slideid) for slideid in lesson.path_extra.split('.')]
            slides_ids.insert(index, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path_extra = path
        lesson.errors_threshold = default_errors_threshold
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    if index == 0:
        lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
    new_slide: Slide = Slide(
        slide_type=SlideType.IMAGE,
        lesson_id=lesson.id,
        picture=slide_picture,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]


@router.post('/new/dict/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_dict_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditDictSlideData, fastui_form(EditDictSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    if source == SlidesMenuType.EXTRA:
        if index == 0:
            lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.PIN_DICT,
            lesson_id=lesson.id,
            text=form.text,
        )
        db_session.add(new_slide)
        await db_session.flush()
        if index == 0:
            path = str(new_slide.id)
            lesson.path_extra = path
        else:
            slides_ids = [int(slideid) for slideid in lesson.path_extra.split('.')]
            slides_ids.insert(index, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path_extra = path
        lesson.errors_threshold = default_errors_threshold
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    if index == 0:
        lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
    new_slide: Slide = Slide(
        slide_type=SlideType.PIN_DICT,
        lesson_id=lesson.id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]


@router.post('/new/quiz_option/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_quiz_option_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizOptionsSlideData, fastui_form(EditQuizOptionsSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    if source == SlidesMenuType.EXTRA:
        if index == 0:
            lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.QUIZ_OPTIONS,
            lesson_id=lesson.id,
            text=form.text,
            right_answers=form.right_answers,
            keyboard=form.keyboard,
            is_exam_slide=form.is_exam_slide,
        )
        db_session.add(new_slide)
        await db_session.flush()
        if index == 0:
            path = str(new_slide.id)
            lesson.path_extra = path
        else:
            slides_ids = [int(slideid) for slideid in lesson.path_extra.split('.')]
            slides_ids.insert(index, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path_extra = path
        lesson.errors_threshold = default_errors_threshold
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    if index == 0:
        lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_OPTIONS,
        lesson_id=lesson.id,
        text=form.text,
        right_answers=form.right_answers,
        keyboard=form.keyboard,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]


@router.post(
    '/new/quiz_input_word/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True
)
async def new_quiz_input_word_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputWordSlideData, fastui_form(EditQuizInputWordSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    if source == SlidesMenuType.EXTRA:
        if index == 0:
            lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.QUIZ_INPUT_WORD,
            lesson_id=lesson.id,
            text=form.text,
            right_answers=form.right_answers,
            is_exam_slide=form.is_exam_slide,
        )
        db_session.add(new_slide)
        await db_session.flush()
        if index == 0:
            path = str(new_slide.id)
            lesson.path_extra = path
        else:
            slides_ids = [int(slideid) for slideid in lesson.path_extra.split('.')]
            slides_ids.insert(index, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path_extra = path
        lesson.errors_threshold = default_errors_threshold
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    if index == 0:
        lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.QUIZ_INPUT_WORD,
            lesson_id=lesson.id,
            text=form.text,
            right_answers=form.right_answers,
            is_exam_slide=form.is_exam_slide,
        )
        db_session.add(new_slide)
        await db_session.flush()
        path = str(new_slide.id)
        lesson.path = path
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_WORD,
        lesson_id=lesson.id,
        text=form.text,
        right_answers=form.right_answers,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]


@router.post(
    '/new/quiz_input_phrase/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True
)
async def new_quiz_input_phrase_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputPhraseSlideData, fastui_form(EditQuizInputPhraseSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    if source == SlidesMenuType.EXTRA:
        if index == 0:
            lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.QUIZ_INPUT_PHRASE,
            lesson_id=lesson.id,
            text=form.text,
            right_answers=form.right_answers,
            almost_right_answers=form.almost_right_answers,
            almost_right_answer_reply=form.almost_right_answer_reply,
            is_exam_slide=form.is_exam_slide,
        )
        db_session.add(new_slide)
        await db_session.flush()
        if index == 0:
            path = str(new_slide.id)
            lesson.path_extra = path
        else:
            slides_ids = [int(slideid) for slideid in lesson.path_extra.split('.')]
            slides_ids.insert(index, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path_extra = path
        lesson.errors_threshold = default_errors_threshold
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    if index == 0:
        lesson: Lesson = await get_lesson_by_id(slide_id, db_session)
        new_slide: Slide = Slide(
            slide_type=SlideType.QUIZ_INPUT_PHRASE,
            lesson_id=lesson.id,
            text=form.text,
            right_answers=form.right_answers,
            almost_right_answers=form.almost_right_answers,
            almost_right_answer_reply=form.almost_right_answer_reply,
            is_exam_slide=form.is_exam_slide,
        )
        db_session.add(new_slide)
        await db_session.flush()
        path = str(new_slide.id)
        lesson.path = path
        await db_session.commit()
        return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
    slides_ids = [int(slideid) for slideid in lesson.path.split('.')]
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_PHRASE,
        lesson_id=lesson.id,
        text=form.text,
        right_answers=form.right_answers,
        almost_right_answers=form.almost_right_answers,
        almost_right_answer_reply=form.almost_right_answer_reply,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]


@router.get('/plus_button/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def add_slide(index: int, slide_id: int, source: SlidesMenuType) -> list[AnyComponent]:
    return get_common_content(
        c.Paragraph(text=''),
        c.Paragraph(text='Выберите тип слайда.'),
        c.Button(
            text='🖋  текст',
            on_click=GoToEvent(url=f'/slides/new/text/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🖼  картинка',
            on_click=GoToEvent(url=f'/slides/new/image/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='📎  словарик',
            on_click=GoToEvent(url=f'/slides/new/pin_dict/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🧨  малый стикер',
            on_click=GoToEvent(url=f'/slides/new/small_sticker/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='💣  большой стикер',
            on_click=GoToEvent(url=f'/slides/new/big_sticker/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🧩  квиз варианты',
            on_click=GoToEvent(url=f'/slides/new/quiz_options/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🗨  квиз впиши слово',
            on_click=GoToEvent(url=f'/slides/new/quiz_input_word/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='💬  квиз впиши фразу',
            on_click=GoToEvent(url=f'/slides/new/quiz_input_phrase/{source}/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='⇦ назад',
            on_click=BackEvent(),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        title=f'Добавить новый слайд',
    )


@router.get('/up_button/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_up_button(
    index: int, slide_id: int, source: SlidesMenuType, db_session: AsyncDBSession
) -> list[AnyComponent]:
    logger.info(f'pressed slide up button with slide id {slide_id} index {index}. source {source}')
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
    if index == 1:
        pass
    else:
        slides_ids[index - 1], slides_ids[index - 2] = slides_ids[index - 2], slides_ids[index - 1]
        path = '.'.join([str(slideid) for slideid in slides_ids])
        if source == SlidesMenuType.REGULAR:
            lesson.path = path
        else:
            lesson.path_extra = path
        await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.get('/down_button/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_down_button(
    index: int, slide_id: int, source: SlidesMenuType, db_session: AsyncDBSession
) -> list[AnyComponent]:
    logger.info(f'pressed slide down button with slide id {slide_id} index {index}. source {source}')
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
    if index == len(slides_ids):
        pass
    else:
        slides_ids[index - 1], slides_ids[index] = slides_ids[index], slides_ids[index - 1]
        path = '.'.join([str(slideid) for slideid in slides_ids])
        if source == SlidesMenuType.REGULAR:
            lesson.path = path
        else:
            lesson.path_extra = path
        await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.get('/delete/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_slide(
    source: SlidesMenuType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
):
    logger.info(f'delete slide with slide id {slide_id} index {index}. source {source}')
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = (
        [int(slideid) for slideid in lesson.path.split('.')]
        if source == SlidesMenuType.REGULAR
        else [int(slideid) for slideid in lesson.path_extra.split('.')]
    )
    del slides_ids[index - 1]
    path = '.'.join([str(slideid) for slideid in slides_ids])
    if source == SlidesMenuType.REGULAR:
        lesson.path = path
    else:
        lesson.path_extra = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@router.get('/confirm_delete/{source}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_slide(
    index: int, slide_id: int, source: SlidesMenuType, db_session: AsyncDBSession
) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    return get_common_content(
        c.Paragraph(text='Вы уверены, что хотите удалить слайд?'),
        c.Div(
            components=[
                c.Link(
                    components=[c.Button(text='Назад', named_style='secondary')],
                    on_click=BackEvent(),
                    class_name='+ ms-2',
                ),
                c.Link(
                    components=[c.Button(text='Удалить', named_style='warning')],
                    on_click=GoToEvent(url=f'/slides/delete/{source}/{index}/{slide_id}/'),
                    class_name='+ ms-2',
                ),
            ]
        ),
        title=f'delete | slide {slide_id} | {slide.slide_type.value}',
    )
