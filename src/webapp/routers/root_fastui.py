import asyncio
from collections import defaultdict
import logging
import mimetypes
from pathlib import Path
from random import randint
from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastui import AnyComponent, FastUI, components as c, prebuilt_html
from fastui.components.display import DisplayLookup, DisplayMode
from fastui.events import BackEvent, GoToEvent, PageEvent
from fastui.forms import SelectSearchResponse, fastui_form

from bot.controllers.slide_controllers import get_slide_by_id, get_slide_by_position
from bot.resources.enums import NavigationObjectType, ReactionType, SlideType
from controllers.misc import get_nav_keyboard
from controllers.reaction import delete_reaction_by_id, get_reactions_table_content
from database.db import AsyncDBSession
from database.models.slide import Slide
from database.schemas.slide import (
    FinalSlideSlideData,
    PinDictSlideData,
    QuizInputPhraseSlideData,
    QuizInputWordSlideData,
    QuizOptionsSlideData,
    ShowImageSlideData,
    TextSlideData,
    get_image_slide_data_model,
    get_text_slide_data_model,
)
from database.schemas.sticker import StickerSlideData
from webapp.routers.components import get_common_content

app = APIRouter()
logger = logging.getLogger()


@app.get('/favicon.ico')
async def favicon():
    file_name = "favicon.ico"
    file_path = Path(f"src/webapp/static/{file_name}")
    return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})


@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
async def root_page() -> list[AnyComponent]:
    logger.info('root router called')
    return get_common_content(c.Paragraph(text=f'test {randint(0, 1000)}'), title='Администрация')


@app.get('/api/slides/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def slide_details_page(slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    prev_slide: Slide = await get_slide_by_position(slide_id, db_session)
    image_component = c.Paragraph(text='')
    match slide.slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            data = StickerSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='slide_type'),
            ]
        case SlideType.TEXT:
            data = TextSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='text'),
                DisplayLookup(field='delay'),
                DisplayLookup(field='keyboard_type'),
            ]
        case SlideType.IMAGE:
            image_component = c.Image(
                src=f'/static/images/lesson_{slide.lesson_id}/{slide.picture}',
                width=600,
                # height=200,
                loading='lazy',
                referrer_policy='no-referrer',
                # class_name='border rounded',
            )
            data = ShowImageSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='picture'),
                DisplayLookup(field='delay'),
                DisplayLookup(field='keyboard_type'),
            ]
        case SlideType.PIN_DICT:
            data = PinDictSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='text'),
            ]
        case SlideType.QUIZ_OPTIONS:
            data = QuizOptionsSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='text'),
                DisplayLookup(field='right_answers'),
                DisplayLookup(field='keyboard'),
                DisplayLookup(field='is_exam_slide'),
            ]
        case SlideType.QUIZ_INPUT_WORD:
            data = QuizInputWordSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='text'),
                DisplayLookup(field='right_answers'),
                DisplayLookup(field='is_exam_slide'),
            ]
        case SlideType.QUIZ_INPUT_PHRASE:
            data = QuizInputPhraseSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='text'),
                DisplayLookup(field='right_answers'),
                DisplayLookup(field='almost_right_answers'),
                DisplayLookup(field='almost_right_answer_reply'),
                DisplayLookup(field='is_exam_slide'),
            ]
        case SlideType.FINAL_SLIDE:
            data = FinalSlideSlideData.model_validate(slide)
            fields = [
                DisplayLookup(field='next_slide'),
                DisplayLookup(field='text', mode=DisplayMode.markdown),
            ]
        case _:
            raise HTTPException(status_code=404, detail="Slide not found")
    return get_common_content(
        # c.Link(components=[c.Button(text='⇦', named_style='secondary')], on_click=BackEvent()),
        c.Div(
            components=get_nav_keyboard(
                mode=NavigationObjectType.SLIDES,
                prev_obj_id=prev_slide.id if prev_slide is not None else None,
                next_obj_id=slide.next_slide if slide and slide.next_slide is not None else None,
            )
        ),
        c.Paragraph(text=''),
        # c.Link(components=[c.Text(text='Back')], on_click=BackEvent()),
        # c.Details(
        #     data=data,
        #     fields=fields,
        #     # class_name='',
        # ),
        c.Div(
            components=[
                image_component if slide.slide_type == SlideType.IMAGE else c.Paragraph(text=''),
                c.Paragraph(text=''),
                c.Details(
                    data=data,
                    fields=fields,
                    # class_name='',
                ),
            ],
            class_name='border-top mt-3 pt-1',
        ),
        c.Div(
            components=[
                c.Link(
                    components=[c.Button(text='Edit slide')],
                    on_click=GoToEvent(url=f'/edit_slide/{slide_id}/'),
                    class_name='+ ms-2',
                ),
            ],
        ),
        title=f'details | slide {slide_id} | {slide.slide_type.value}',
    )


@app.get('/api/edit_slide/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_slide(slide_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    image_model = get_image_slide_data_model(slide.lesson_id)
    match slide.slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            submit_url = f'/api/edit_slide/sticker/{slide_id}/'
            form = c.ModelForm(model=StickerSlideData, submit_url=submit_url)
        case SlideType.TEXT:
            submit_url = f'/api/edit_slide/text/{slide_id}/'
            form = c.ModelForm(model=get_text_slide_data_model(slide), submit_url=submit_url)
        case SlideType.IMAGE:
            submit_url = f'/api/edit_slide/image/{slide.lesson_id}/{slide_id}/'
            form = c.ModelForm(model=image_model, submit_url=submit_url)
        case SlideType.PIN_DICT:
            submit_url = f'/api/edit_slide/dict/{slide_id}/'
            form = c.ModelForm(model=PinDictSlideData, submit_url=submit_url)
        case SlideType.QUIZ_OPTIONS:
            submit_url = f'/api/edit_slide/quiz_option/{slide_id}/'
            form = c.ModelForm(model=QuizOptionsSlideData, submit_url=submit_url)
        case SlideType.QUIZ_INPUT_WORD:
            submit_url = f'/api/edit_slide/quiz_input_word/{slide_id}/'
            form = c.ModelForm(model=QuizInputWordSlideData, submit_url=submit_url)
        case SlideType.QUIZ_INPUT_PHRASE:
            submit_url = f'/api/edit_slide/quiz_input_phrase/{slide_id}/'
            form = c.ModelForm(model=QuizInputPhraseSlideData, submit_url=submit_url)
        case SlideType.FINAL_SLIDE:
            submit_url = f'/api/edit_slide/final/{slide_id}/'
            form = c.ModelForm(model=FinalSlideSlideData, submit_url=submit_url)
        case _:
            raise HTTPException(status_code=404, detail="Slide not found")
    return get_common_content(
        c.Link(components=[c.Button(text='⇦', named_style='secondary')], on_click=BackEvent()),
        c.Paragraph(text=''),
        c.Paragraph(text=f'IMAGE HERE'),
        form,
        title=f'edit | slide {slide_id} | {slide.slide_type.value}',
    )


@app.get('/api/files/{lesson_id}/', response_model=SelectSearchResponse)
async def search_view(lesson_id: int) -> SelectSearchResponse:
    files = defaultdict(list)
    directory = Path(f"src/webapp/static/images/lesson_{lesson_id}")
    for file in directory.iterdir():
        mime_type, _ = mimetypes.guess_type(file)
        if mime_type in ['image/png', 'image/jpeg', 'image/gif', 'image/heic', 'image/tiff', 'image/webp']:
            file_name = file.stem.replace("-", "_").replace(" ", "_")
            files[mime_type].append({'value': mime_type, 'label': file_name})
    options = [{'label': k, 'options': v} for k, v in files.items()]
    return SelectSearchResponse(options=options)


@app.post('/api/edit_slide/sticker/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_sticker_slide(
    slide_id: int, db_session: AsyncDBSession, form: Annotated[StickerSlideData, fastui_form(StickerSlideData)]
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.slide_type = form.slide_type
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.post('/api/edit_slide/text/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
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


@app.post('/api/edit_slide/image/{lesson_id}/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
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


@app.post('/api/edit_slide/dict/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
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


@app.post('/api/edit_slide/quiz_option/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
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


@app.post('/api/edit_slide/quiz_input_word/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
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


@app.post('/api/edit_slide/quiz_input_phrase/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
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


@app.post('/api/edit_slide/final/{slide_id}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_final_slide(
    slide_id: int, db_session: AsyncDBSession, form: Annotated[FinalSlideSlideData, fastui_form(FinalSlideSlideData)]
):
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    slide.next_slide = form.next_slide
    slide.text = form.text
    await db_session.commit()
    return [c.FireEvent(event=GoToEvent(url=f'/lesson_{slide.lesson_id}/slides'))]


@app.post('/api/reactions/{reaction_id}/delete/', response_model=FastUI, response_model_exclude_none=True)
async def delete_reaction(
    reaction_id: int,
    db_session: AsyncDBSession,
):
    await delete_reaction_by_id(reaction_id, db_session)
    return [c.FireEvent(event=GoToEvent(url=f'/reactions'))]


@app.get("/api/texts", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page() -> list[AnyComponent]:
    logger.info('slides router called')
    return get_common_content(title='Тексты')


@app.get("/api/reactions", response_model=FastUI, response_model_exclude_none=True)
async def lessons_page(db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    right_reactions = await get_reactions_table_content(ReactionType.RIGHT, db_session)
    wrong_reactions = await get_reactions_table_content(ReactionType.WRONG, db_session)
    return get_common_content(
        c.Div(
            components=[
                c.Heading(text='RIGHT', level=4),
                c.Button(text='➕', named_style='secondary', on_click=GoToEvent(url=f'/slides/{777}/')),
            ]
        ),
        # c.Div(components=components_right),
        c.Paragraph(text=''),
        c.Table(
            data=right_reactions,
            columns=[
                # DisplayLookup(field='id', table_width_percent=3, on_click=GoToEvent(url='/reactions/{id}/')),
                DisplayLookup(field='text', title='text'),
                DisplayLookup(
                    field='edit_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/modal-prompt/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='minus_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/modal-prompt/{id}'),
                    table_width_percent=3,
                ),
            ],
        ),
        c.Paragraph(text=''),
        c.Div(
            components=[
                c.Heading(text='WRONG', level=4),
                c.Button(
                    text='➕',
                    named_style='secondary',
                    on_click=GoToEvent(url=f'/slides/{777}/'),
                ),
            ]
        ),
        c.Paragraph(text=''),
        c.Table(
            data=wrong_reactions,
            columns=[
                DisplayLookup(field='text', title='text'),
                DisplayLookup(
                    field='edit_button',
                    title=' ',
                    on_click=GoToEvent(url='/reactions/modal-prompt/'),
                    table_width_percent=3,
                ),
                DisplayLookup(
                    field='minus_button',
                    title=' ',
                    on_click=PageEvent(name='modal-prompt'),
                    table_width_percent=3,
                ),
            ],
        ),
        c.Modal(
            title='Удаление реакции',
            body=[
                c.Paragraph(text='Вы действительно хотите удалить реакцию?'),
                c.Form(
                    form_fields=[],
                    submit_url='/api/reactions/modal-prompt/{id}',
                    loading=[c.Spinner(text=f'Deleting reaction...')],
                    footer=[],
                    submit_trigger=PageEvent(name='modal-form-submit'),
                ),
            ],
            footer=[
                c.Button(text='Cancel', named_style='secondary', on_click=PageEvent(name='modal-prompt', clear=True)),
                c.Button(text='Submit', on_click=PageEvent(name='modal-form-submit')),
            ],
            open_trigger=PageEvent(name='modal-prompt'),
        ),
        title='Реакции',
    )


@app.post('/api/reactions/modal-prompt/{reaction_id}/', response_model=FastUI, response_model_exclude_none=True)
async def modal_prompt_submit(reaction_id: int) -> list[AnyComponent]:
    await asyncio.sleep(0.5)
    # reaction_id = event.context.get('reaction_id')

    print(f'deleting reaction...{reaction_id}')

    # await delete_reaction_by_id()
    return [c.FireEvent(event=PageEvent(name='modal-prompt', clear=True))]


@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    return HTMLResponse(prebuilt_html(title='English buddy FastUI'))
