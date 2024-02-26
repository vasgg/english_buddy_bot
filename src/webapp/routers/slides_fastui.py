import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.exceptions import ResponseValidationError
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup, DisplayMode
from fastui.events import BackEvent, GoToEvent
from fastui.forms import fastui_form

from bot.controllers.lesson_controllers import update_lesson_first_slide
from bot.controllers.slide_controllers import get_slide_by_id
from bot.resources.enums import SlideType
from controllers.slide import get_all_slides_from_lesson_by_order, get_all_slides_from_lesson_by_order_fastui
from database.db import AsyncDBSession
from database.models.slide import Slide
from database.schemas.slide import (
    FinalSlideSlideData,
    LessonPickerData,
    PinDictSlideData,
    QuizInputPhraseSlideData,
    QuizInputWordSlideData,
    QuizOptionsSlideData,
    TextSlideData,
    get_final_slide_slide_data_model,
    get_image_slide_data_model,
    get_pin_dict_slide_data_model,
    get_quiz_input_phrase_slide_data_model,
    get_quiz_input_word_slide_data_model,
    get_quiz_options_slide_data_model,
    get_text_slide_data_model,
)
from database.schemas.sticker import StickerSlideData
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get("/lesson{lesson_id}", response_model=FastUI, response_model_exclude_none=True)
async def slides_page(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    slides = await get_all_slides_from_lesson_by_order_fastui(lesson_id, db_session)
    '/api/lessons/'
    submit_url = f'/api/slides/lesson_{lesson_id}'
    form = c.ModelForm(model=LessonPickerData, submit_url=submit_url)
    return get_common_content(
        c.Paragraph(text=''),
        form,
        # c.Heading(text='Lesson 1', level=2),
        # c.Div(
        #     components=[
        #         c.Button(text='◀︎', named_style='secondary', class_name='+ ms-2'),
        #         c.Button(text='▶︎', named_style='warning', on_click=PageEvent(name='static-modal')),
        #     ]
        # ),
        c.Paragraph(text=''),
        c.Table(
            data=slides,
            columns=[
                DisplayLookup(
                    field='index',
                    table_width_percent=3,
                ),
                # DisplayLookup(
                #     field='id',
                #     table_width_percent=3,
                # ),
                # DisplayLookup(
                #     field='next_slide',
                #     table_width_percent=3,
                # ),
                DisplayLookup(
                    field='emoji',
                    table_width_percent=3,
                ),
                DisplayLookup(field='text', mode=DisplayMode.plain),
                DisplayLookup(field='details', table_width_percent=20),
                DisplayLookup(field='is_exam_slide', table_width_percent=3),
                DisplayLookup(
                    field='edit_button',
                    mode=DisplayMode.plain,
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
            form = c.ModelForm(model=StickerSlideData, submit_url=submit_url)
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
            submit_url = f'/api/slides/edit/image/{slide.lesson_id}/{slide_id}/'
            form = c.ModelForm(model=get_image_slide_data_model(slide.lesson_id), submit_url=submit_url)
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
    slide_id: int, db_session: AsyncDBSession, form: Annotated[StickerSlideData, fastui_form(StickerSlideData)]
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    for field in form.model_fields.keys():
        form_value = getattr(form, field, None)
        if form_value is not None:
            setattr(slide, field, form_value)
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.post('/edit/text/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_text_slide(
    slide_id: int, db_session: AsyncDBSession, form: Annotated[TextSlideData, fastui_form(TextSlideData)]
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    slide.delay = form.delay
    slide.keyboard_type = form.keyboard_type
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.post('/edit/{lesson_id}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_image_slide(
    lesson_id: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[get_image_slide_data_model(0), fastui_form(TextSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    slide.delay = form.delay
    slide.keyboard_type = form.keyboard_type
    # TODO: check if image uploaded
    slide.picture = form.select_picture

    # slide.picture = form.select_picture
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{lesson_id}/slides'))]


@app.post('/edit/dict/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_dict_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[PinDictSlideData, fastui_form(PinDictSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.post('/edit/quiz_option/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_option_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[QuizOptionsSlideData, fastui_form(QuizOptionsSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    slide.right_answers = form.right_answers
    slide.keyboard = form.keyboard
    slide.is_exam_slide = form.is_exam_slide
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/api/lesson_{slide.lesson_id}/slides'))]


@app.post('/edit/quiz_input_word/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_input_word_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[QuizInputWordSlideData, fastui_form(QuizInputWordSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    slide.right_answers = form.right_answers
    slide.is_exam_slide = form.is_exam_slide
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.post('/edit/quiz_input_phrase/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_input_phrase_slide(
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[QuizInputPhraseSlideData, fastui_form(QuizInputPhraseSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    slide.right_answers = form.right_answers
    slide.almost_right_answers = form.almost_right_answers
    slide.almost_right_answers_reply = form.almost_right_answers_reply
    slide.is_exam_slide = form.is_exam_slide
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.post('/edit/final/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_final_slide(
    slide_id: int, db_session: AsyncDBSession, form: Annotated[FinalSlideSlideData, fastui_form(FinalSlideSlideData)]
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.get('/up_button/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_up_button(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed slide up button with slide id {slide_id} index {index}')
    slide = await get_slide_by_id(slide_id, db_session)
    all_slides = await get_all_slides_from_lesson_by_order(slide.lesson_id, db_session)
    try:
        if index <= 1:
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
        await db_session.commit()
    except ResponseValidationError:
        pass
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}'))]


@app.get('/down_button/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_down_button(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed slide down button with slide id {slide_id} index {index}')
    slide = await get_slide_by_id(slide_id, db_session)
    all_slides = await get_all_slides_from_lesson_by_order(slide.lesson_id, db_session)
    next_slide = all_slides[index]
    try:
        if index == len(all_slides):
            pass
        elif index == 1:
            await update_lesson_first_slide(slide.lesson_id, next_slide.id, db_session)
            temp2 = next_slide.next_slide
            slide.next_slide = None
            next_slide.next_slide = None
            await db_session.flush()
            next_slide.next_slide = slide.id
            slide.next_slide = temp2

        elif index == 2:
            temp = slide.next_slide
            temp2 = next_slide.next_slide
            slide.next_slide = None
            next_slide.next_slide = None
            await db_session.flush()
            slide.next_slide = temp2
            next_slide.next_slide = slide.id
        else:
            ...
        await db_session.commit()
    except ResponseValidationError:
        pass
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson1'))]
