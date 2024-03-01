import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent
from fastui.forms import fastui_form

from bot.controllers.lesson_controllers import update_lesson_first_slide
from bot.controllers.slide_controllers import get_slide_by_id
from bot.resources.enums import SlideType
from controllers.slide import get_all_slides_from_lesson_by_order, get_all_slides_from_lesson_by_order_fastui
from database.db import AsyncDBSession
from database.models.slide import Slide
from database.schemas.slide import (
    EditDictSlideData,
    EditFinalSlideSlideData,
    EditImageSlideData,
    EditQuizInputPhraseSlideData,
    EditQuizInputWordSlideData,
    EditQuizOptionsSlideData,
    EditTextSlideDataModel,
    get_final_slide_slide_data_model,
    get_image_slide_data_model,
    get_pin_dict_slide_data_model,
    get_quiz_input_phrase_slide_data_model,
    get_quiz_input_word_slide_data_model,
    get_quiz_options_slide_data_model,
    get_text_slide_data_model,
)
from database.schemas.sticker import EditStickerSlideDataModel, get_sticker_slide_data_model
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get("/lesson{lesson_id}/", response_model=FastUI, response_model_exclude_none=True)
async def slides_page(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    slides = await get_all_slides_from_lesson_by_order_fastui(lesson_id, db_session)
    return get_common_content(
        c.Paragraph(text=''),
        c.Table(
            data=slides,
            columns=[
                DisplayLookup(
                    field='index',
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='emoji',
                    table_width_percent=3,
                ),
                DisplayLookup(field='text'),
                DisplayLookup(field='details', table_width_percent=20),
                DisplayLookup(field='is_exam_slide', table_width_percent=3),
                DisplayLookup(
                    field='edit_button',
                    on_click=GoToEvent(url='/slides/edit/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='up_button', on_click=GoToEvent(url='/slides/up_button/{index}/{id}/'), table_width_percent=3
                ),
                DisplayLookup(
                    field='down_button',
                    on_click=GoToEvent(url='/slides/down_button/{index}/{id}/'),
                    table_width_percent=3,
                ),
                DisplayLookup(field='plus_button', table_width_percent=3),
                DisplayLookup(field='minus_button', table_width_percent=3),
            ],
        ),
        title='Слайды',
    )


@app.get('/edit/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_slide(slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    optionnal_component = c.Paragraph(text='')
    match slide.slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            submit_url = f'/api/slides/edit/sticker/{slide_id}/'
            form = c.ModelForm(model=get_sticker_slide_data_model(slide), submit_url=submit_url)
        case SlideType.TEXT:
            submit_url = f'/api/slides/edit/text/{slide_id}/'
            form = c.ModelForm(model=get_text_slide_data_model(slide), submit_url=submit_url)
        case SlideType.IMAGE:
            optionnal_component = c.Image(
                src=f'/static/images/lesson_{slide.lesson_id}/{slide.picture}',
                width=600,
                # height=200,
                loading='lazy',
                referrer_policy='no-referrer',
                # class_name='border rounded',
            )
            submit_url = f'/api/slides/edit/image/{slide_id}/'
            form = c.ModelForm(model=get_image_slide_data_model(slide), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/slides/edit/dict/{slide_id}/'
            form = c.ModelForm(model=get_pin_dict_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/slides/edit/quiz_option/{slide_id}/'
            form = c.ModelForm(model=get_quiz_options_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/slides/edit/quiz_input_word/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/slides/edit/quiz_input_phrase/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(slide), submit_url=submit_url)
        case SlideType.FINAL_SLIDE:
            submit_url = f'/api/slides/edit/final/{slide_id}/'
            form = c.ModelForm(model=get_final_slide_slide_data_model(slide), submit_url=submit_url)
        case _:
            raise HTTPException(status_code=404, detail="Unexpected slide type")
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=''),
        optionnal_component,
        form,
        title=f'edit | slide {slide_id} | {slide.slide_type.value}',
    )


@app.post('/edit/sticker/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_sticker_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditStickerSlideDataModel, fastui_form(EditStickerSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/text/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_text_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditTextSlideDataModel, fastui_form(EditTextSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/dict/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_dict_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditDictSlideData, fastui_form(EditDictSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/quiz_option/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_option_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizOptionsSlideData, fastui_form(EditQuizOptionsSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/quiz_input_word/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_input_word_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputWordSlideData, fastui_form(EditQuizInputWordSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/quiz_input_phrase/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_input_phrase_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputPhraseSlideData, fastui_form(EditQuizInputPhraseSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/final/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_final_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditFinalSlideSlideData, fastui_form(EditFinalSlideSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/image/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_image_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditImageSlideData, fastui_form(EditImageSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    print(form)
    if form.upload_new_picture != '':
        if form.next_slide is not None:
            slide.next_slide = form.next_slide
        if form.delay is not None:
            slide.delay = form.delay
        if form.keyboard_type is not None:
            slide.keyboard_type = form.keyboard_type
        if form.select_picture is not None:
            slide.picture = form.select_picture
    else:
        if form.next_slide is not None:
            slide.next_slide = form.next_slide
        if form.delay is not None:
            slide.delay = form.delay
        if form.keyboard_type is not None:
            slide.keyboard_type = form.keyboard_type
        if form.upload_new_picture is not None:
            slide.picture = form.upload_new_picture
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.get('/up_button/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_up_button(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed slide up button with slide id {slide_id} index {index}')
    slide = await get_slide_by_id(slide_id, db_session)
    all_slides = await get_all_slides_from_lesson_by_order(slide.lesson_id, db_session)
    if index == 1:
        pass
    elif index == 2:
        slide_minus_1: Slide = all_slides[index - 2]
        temp = slide.next_slide
        slide.next_slide = None
        slide_minus_1.next_slide = None
        await db_session.flush()
        slide.next_slide = slide_minus_1.id
        slide_minus_1.next_slide = temp
        await update_lesson_first_slide(slide.lesson_id, slide.id, db_session)
    else:
        slide_minus_2: Slide = all_slides[index - 3]
        slide_minus_1: Slide = all_slides[index - 2]
        temp = slide.next_slide
        slide.next_slide = None
        slide_minus_1.next_slide = None
        slide_minus_2.next_slide = None
        await db_session.flush()
        slide_minus_2.next_slide = slide.id
        slide.next_slide = slide_minus_1.id
        slide_minus_1.next_slide = temp
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.get('/down_button/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_down_button(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed slide down button with slide id {slide_id} index {index}')
    slide = await get_slide_by_id(slide_id, db_session)
    all_slides = await get_all_slides_from_lesson_by_order(slide.lesson_id, db_session)
    if index == len(all_slides):
        logger.info(f'pressed down button on last slide with slide id {slide_id} index {index}')
        pass
    elif index == len(all_slides) - 1:
        slide_minus_1: Slide = all_slides[index - 2]
        next_slide = all_slides[index]
        slide.next_slide = None
        await db_session.flush()
        slide_minus_1.next_slide = next_slide.id
        next_slide.next_slide = slide.id
    elif index == 1:
        next_slide = all_slides[index]
        temp = next_slide.next_slide
        slide.next_slide = None
        next_slide.next_slide = None
        await db_session.flush()
        slide.next_slide = temp
        next_slide.next_slide = slide.id
        await update_lesson_first_slide(slide.lesson_id, next_slide.id, db_session)
    else:
        slide_minus_1: Slide = all_slides[index - 2]
        next_slide = all_slides[index]
        temp = next_slide.next_slide
        slide.next_slide = None
        slide_minus_1.next_slide = None
        next_slide.next_slide = None
        await db_session.flush()
        slide_minus_1.next_slide = next_slide.id
        slide.next_slide = temp
        next_slide.next_slide = slide.id
    # await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]
