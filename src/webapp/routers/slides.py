import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastui import AnyComponent, FastUI, components as c
from fastui.components.display import DisplayLookup
from fastui.events import BackEvent, GoToEvent
from fastui.forms import fastui_form

from database.crud.lesson import get_lesson_by_id
from database.crud.slide import get_slide_by_id
from database.db import AsyncDBSession
from database.models.lesson import Lesson
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
from enums import KeyboardType, SlideType, StickerType
from webapp.controllers.slide import get_all_slides_from_lesson_by_order_fastui
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get("/lesson{lesson_id}/", response_model=FastUI, response_model_exclude_none=True)
async def slides_page(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    slides = await get_all_slides_from_lesson_by_order_fastui(lesson.path, db_session)
    if len(slides) == 0:
        return get_common_content(
            c.Paragraph(text=''),
            c.Paragraph(text='There is no slides yet'),
            title='Слайды',
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
                field='edit_button', on_click=GoToEvent(url='/slides/edit/{index}/{id}/'), table_width_percent=3
            ),
            DisplayLookup(
                field='up_button', on_click=GoToEvent(url='/slides/up_button/{index}/{id}/'), table_width_percent=3
            ),
            DisplayLookup(
                field='down_button', on_click=GoToEvent(url='/slides/down_button/{index}/{id}/'), table_width_percent=3
            ),
            DisplayLookup(
                field='plus_button', on_click=GoToEvent(url='/slides/plus_button/{index}/{id}/'), table_width_percent=3
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/slides/confirm_delete/{index}/{id}/'),
                table_width_percent=3,
            ),
        ],
    )

    return get_common_content(
        c.Paragraph(text=''),
        slides_table,
        title='Слайды',
    )


@app.get('/edit/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_slide(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    optionnal_component = c.Paragraph(text='')
    match slide.slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            submit_url = f'/api/slides/edit/sticker/{index}/{slide_id}/'
            form = c.ModelForm(model=get_sticker_slide_data_model(slide), submit_url=submit_url)
        case SlideType.TEXT:
            submit_url = f'/api/slides/edit/text/{index}/{slide_id}/'
            form = c.ModelForm(model=get_text_slide_data_model(slide), submit_url=submit_url)
        case SlideType.IMAGE:
            optionnal_component = c.Image(
                src=f'/static/lessons_images/{slide.lesson_id}/{slide.picture}',
                width=600,
                # height=200,
                loading='lazy',
                referrer_policy='no-referrer',
                # class_name='border rounded',
            )
            submit_url = f'/api/slides/edit/image/{index}/{slide_id}/'
            form = c.ModelForm(model=get_image_slide_data_model(slide), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/slides/edit/dict/{index}/{slide_id}/'
            form = c.ModelForm(model=get_pin_dict_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/slides/edit/quiz_option/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_options_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/slides/edit/quiz_input_word/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(slide), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/slides/edit/quiz_input_phrase/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(slide), submit_url=submit_url)
        case SlideType.FINAL_SLIDE:
            submit_url = f'/api/slides/edit/final_slide/{index}/{slide_id}/'
            form = c.ModelForm(model=get_final_slide_slide_data_model(slide), submit_url=submit_url)
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


@app.post('/edit/sticker/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_sticker_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditStickerSlideDataModel, fastui_form(EditStickerSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]

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
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/text/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_text_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditTextSlideDataModel, fastui_form(EditTextSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.TEXT,
        lesson_id=slide.lesson_id,
        text=form.text,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/dict/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_dict_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditDictSlideData, fastui_form(EditDictSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.PIN_DICT,
        lesson_id=slide.lesson_id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/quiz_option/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_option_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizOptionsSlideData, fastui_form(EditQuizOptionsSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_OPTIONS,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        keyboard_type=form.keyboard_type,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/quiz_input_word/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_input_word_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputWordSlideData, fastui_form(EditQuizInputWordSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
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
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/quiz_input_phrase/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_quiz_input_phrase_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputPhraseSlideData, fastui_form(EditQuizInputPhraseSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_PHRASE,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        almost_right_answers=form.almost_right_answers,
        almost_right_answers_reply=form.almost_right_answers_reply,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/final/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_final_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditFinalSlideSlideData, fastui_form(EditFinalSlideSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.FINAL_SLIDE,
        lesson_id=slide.lesson_id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/edit/image/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_image_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditImageSlideData, fastui_form(EditImageSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    # allowed_image_formats = ['png', 'jpg', 'jpeg', 'gif', 'heic', 'tiff', 'webp']
    # if form.upload_new_picture.filename:
    #     if form.upload_new_picture.filename.rsplit('.', 1)[1].lower() in allowed_image_formats:
    #         directory = Path(f"src/webapp/static/lessons_images/{slide.lesson_id}")
    #         directory.mkdir(parents=True, exist_ok=True)
    #         image_data = await form.upload_new_picture.read()
    #         image = Image.open(io.BytesIO(image_data))
    #         if image.width > 800:
    #             new_height = int((800 / image.width) * image.height)
    #             image = image.resize((800, new_height), Image.Resampling.LANCZOS)
    #         file_path = directory / form.upload_new_picture.filename
    #         with open(file_path, "wb") as buffer:
    #             image_format = form.upload_new_picture.content_type
    #             image.save(buffer, format=image_format.split("/")[1])
    #
    #         slide_picture = form.upload_new_picture.filename
    # else:
    slide_picture = form.select_picture
    new_slide: Slide = Slide(
        slide_type=SlideType.IMAGE,
        lesson_id=slide.lesson_id,
        picture=slide_picture,
        delay=form.delay,
        keyboard_type=form.keyboard_type,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids[index] = new_slide.id
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.get('/new/{slide_type}/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def create_slide(
    slide_type: SlideType,
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    match slide_type:
        case SlideType.TEXT:
            submit_url = f'/api/slides/new/text/{index}/{slide_id}/'
            form = c.ModelForm(model=get_text_slide_data_model(), submit_url=submit_url)
        case SlideType.IMAGE:
            submit_url = f'/api/slides/new/image/{index}/{slide_id}/'
            form = c.ModelForm(model=get_image_slide_data_model(lesson_id=slide.lesson_id), submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/slides/new/dict/{index}/{slide_id}/'
            form = c.ModelForm(model=get_pin_dict_slide_data_model(), submit_url=submit_url)
        case SlideType.SMALL_STICKER:
            lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
            slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
            new_slide: Slide = Slide(
                slide_type=SlideType.SMALL_STICKER,
                lesson_id=slide.lesson_id,
            )
            db_session.add(new_slide)
            await db_session.flush()
            slides_ids.insert(index + 1, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path = path
            await db_session.commit()
            return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]
        case SlideType.BIG_STICKER:
            lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
            slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
            new_slide: Slide = Slide(
                slide_type=SlideType.BIG_STICKER,
                lesson_id=slide.lesson_id,
            )
            db_session.add(new_slide)
            await db_session.flush()
            slides_ids.insert(index + 1, new_slide.id)
            path = '.'.join([str(slideid) for slideid in slides_ids])
            lesson.path = path
            await db_session.commit()
            return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/slides/new/quiz_option/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_options_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/slides/new/quiz_input_word/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_word_slide_data_model(), submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/slides/new/quiz_input_phrase/{index}/{slide_id}/'
            form = c.ModelForm(model=get_quiz_input_phrase_slide_data_model(), submit_url=submit_url)
        case SlideType.FINAL_SLIDE:
            submit_url = f'/api/slides/new/final_slide/{index}/{slide_id}/'
            form = c.ModelForm(model=get_final_slide_slide_data_model(), submit_url=submit_url)
        case _:
            assert False, 'Unexpected slide type'
    return get_common_content(
        c.Link(components=[c.Button(text='Назад', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=f''),
        form,
        title=f'Создание слайда | {slide_type.value}',
    )


@app.post('/new/text/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_text_slide_form(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditTextSlideDataModel, fastui_form(EditTextSlideDataModel)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.TEXT,
        lesson_id=slide.lesson_id,
        text=form.text,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index + 1, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/new/image/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_image_slide_form(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditImageSlideData, fastui_form(EditImageSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.IMAGE,
        lesson_id=slide.lesson_id,
        picture=form.select_picture,
        delay=form.delay,
        keyboard_type=KeyboardType.FURTHER if form.keyboard_type else None,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index + 1, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/new/dict/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_dict_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditDictSlideData, fastui_form(EditDictSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.PIN_DICT,
        lesson_id=slide.lesson_id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index + 1, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/new/quiz_option/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_quiz_option_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizOptionsSlideData, fastui_form(EditQuizOptionsSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_OPTIONS,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        keyboard=form.keyboard,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index + 1, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/new/quiz_input_word/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_quiz_input_word_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputWordSlideData, fastui_form(EditQuizInputWordSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.QUIZ_INPUT_WORD,
        lesson_id=slide.lesson_id,
        text=form.text,
        right_answers=form.right_answers,
        is_exam_slide=form.is_exam_slide,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index + 1, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/new/quiz_input_phrase/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_quiz_input_phrase_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditQuizInputPhraseSlideData, fastui_form(EditQuizInputPhraseSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
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
    slides_ids.insert(index + 1, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.post('/new/final_slide/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def new_final_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
    form: Annotated[EditFinalSlideSlideData, fastui_form(EditFinalSlideSlideData)],
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    new_slide: Slide = Slide(
        slide_type=SlideType.FINAL_SLIDE,
        lesson_id=slide.lesson_id,
        text=form.text,
    )
    db_session.add(new_slide)
    await db_session.flush()
    slides_ids.insert(index + 1, new_slide.id)
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.get('/plus_button/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def add_slide(index: int, slide_id: int) -> list[AnyComponent]:
    return get_common_content(
        c.Paragraph(text=''),
        c.Paragraph(text='Выберите тип слайда.'),
        c.Button(
            text='🖋  текст',
            on_click=GoToEvent(url=f'/slides/new/text/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🖼  картинка',
            on_click=GoToEvent(url=f'/slides/new/image/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='📎  словарик',
            on_click=GoToEvent(url=f'/slides/new/pin_dict/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🧨  малый стикер',
            on_click=GoToEvent(url=f'/slides/new/small_sticker/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='💣  большой стикер',
            on_click=GoToEvent(url=f'/slides/new/big_sticker/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🧩  квиз варианты',
            on_click=GoToEvent(url=f'/slides/new/quiz_options/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🗨  квиз впиши слово',
            on_click=GoToEvent(url=f'/slides/new/quiz_input_word/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='💬  квиз впиши фразу',
            on_click=GoToEvent(url=f'/slides/new/quiz_input_phrase/{index}/{slide_id}/'),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🎉  финальный слайд',
            on_click=GoToEvent(url=f'/slides/new/final_slide/{index}/{slide_id}/'),
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


@app.get('/up_button/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_up_button(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed slide up button with slide id {slide_id} index {index}')
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    if index == 1:
        pass
    else:
        slides_ids[index], slides_ids[index - 1] = slides_ids[index - 1], slides_ids[index]
        path = '.'.join([str(slideid) for slideid in slides_ids])
        lesson.path = path
        await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.get('/down_button/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slides_down_button(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info(f'pressed slide down button with slide id {slide_id} index {index}')
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    if index == len(slides_ids) - 1:
        pass
    else:
        slides_ids[index], slides_ids[index + 1] = slides_ids[index + 1], slides_ids[index]
        path = '.'.join([str(slideid) for slideid in slides_ids])
        lesson.path = path
        await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.get('/delete/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_slide(
    index: int,
    slide_id: int,
    db_session: AsyncDBSession,
):
    logger.info(f'delete slide with slide id {slide_id} index {index}')
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    lesson: Lesson = await get_lesson_by_id(slide.lesson_id, db_session)
    slides_ids = [int(slideid) for slideid in lesson.path.split('.') if slideid]
    del slides_ids[index]
    path = '.'.join([str(slideid) for slideid in slides_ids])
    lesson.path = path
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{slide.lesson_id}/'))]


@app.get('/confirm_delete/{index}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def delete_slide(index: int, slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
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
                    on_click=GoToEvent(url=f'/slides/delete/{index}/{slide_id}/'),
                    class_name='+ ms-2',
                ),
            ]
        ),
        title=f'delete | slide {slide_id} | {slide.slide_type.value}',
    )
