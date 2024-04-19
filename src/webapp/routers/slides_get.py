import logging

from fastapi import APIRouter
from fastui import AnyComponent, FastUI
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent

from database.crud.lesson import get_lesson_by_id
from database.crud.slide import get_slide_by_id
from database.models.lesson import Lesson
from database.models.slide import Slide
from enums import MoveSlideDirection, PathType, SlideType, SlidesMenuType, StickerType
from webapp.consts import ERRORS_THRESHOLD, IMAGE_WIDTH
from webapp.controllers.slide import (
    create_new_sticker,
    delete_slide,
    get_all_slides_from_lesson_by_order_fastui,
    get_edit_slide_form_by_slide_type,
    get_new_slide_form_by_slide_type,
    move_slide,
    update_lesson_path,
)
from webapp.db import AsyncDBSession
from webapp.routers.components.main_component import back_button, get_common_content
from webapp.schemas.slide import (
    get_image_slide_data_model,
)
from webapp.schemas.sticker import get_sticker_slide_data_model

router = APIRouter()
logger = logging.getLogger()


@router.get("/lesson{lesson_id}/", response_model=FastUI, response_model_exclude_none=True)
async def slides_page(lesson_id: int, db_session: AsyncDBSession) -> list[AnyComponent]:
    logger.info('slides router called')
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    slides = await get_all_slides_from_lesson_by_order_fastui(db_session, lesson.path)
    if not slides:
        return get_common_content(
            c.Paragraph(text=''),
            c.Paragraph(text='В этом уроке ещё нет слайдов.'),
            back_button,
            c.Paragraph(text=''),
            c.Button(text='Создать слайд', on_click=GoToEvent(url=f'/slides/plus_button/regular/{lesson_id}/')),
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
                on_click=GoToEvent(url='/slides/edit/regular/{slide_type}/{id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='up_button',
                on_click=GoToEvent(url='/slides/up/regular/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='down_button',
                on_click=GoToEvent(url='/slides/down/regular/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='plus_button',
                on_click=GoToEvent(url='/slides/plus_button/regular/{lesson_id}/?index={index}'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/slides/confirm_delete/regular/{id}/{index}/'),
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
            c.Button(text='Создать экстра слайд', on_click=GoToEvent(url=f'/slides/plus_button/extra/{lesson_id}/')),
            c.Paragraph(text=''),
            title=f'Слайды | Урок {lesson.index} | {lesson.title}',
        )
    extra_slides = await get_all_slides_from_lesson_by_order_fastui(db_session, str(lesson.path_extra))
    extra_slides_table = c.Table(
        data=extra_slides,
        columns=[
            DisplayLookup(field='index', table_width_percent=3),
            DisplayLookup(field='emoji', table_width_percent=3),
            DisplayLookup(field='text'),
            DisplayLookup(field='details', table_width_percent=23),
            DisplayLookup(
                field='edit_button',
                on_click=GoToEvent(url='/slides/edit/extra/{slide_type}/{id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='up_button',
                on_click=GoToEvent(url='/slides/up/extra/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='down_button',
                on_click=GoToEvent(url='/slides/down/extra/{lesson_id}/{index}/'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='plus_button',
                on_click=GoToEvent(url='/slides/plus_button/extra/{lesson_id}/?index={index}'),
                table_width_percent=3,
            ),
            DisplayLookup(
                field='minus_button',
                on_click=GoToEvent(url='/slides/confirm_delete/extra/{id}/{index}/'),
                table_width_percent=3,
            ),
        ],
    )
    return get_common_content(
        c.Paragraph(text=''),
        slides_table,
        c.Paragraph(text=''),
        c.Heading(text='Экстра слайды', level=3),
        c.Paragraph(text=''),
        extra_slides_table,
        title=f'Слайды | Урок {lesson.index} | {lesson.title}',
    )


@router.get('/plus_button/{source}/{lesson_id}/', response_model=FastUI, response_model_exclude_none=True)
async def add_slide(lesson_id: int, source: SlidesMenuType, index: int | None = None) -> list[AnyComponent]:
    suffix = f'{index}/' if index else ''
    return get_common_content(
        c.Paragraph(text=''),
        c.Paragraph(text='Выберите тип слайда.'),
        c.Paragraph(text=''),
        c.Button(
            text='🖋  текст',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/text/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🖼  картинка',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/image/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='📎  словарик',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/dict/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🧨  малый стикер',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/small_sticker/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='💣  большой стикер',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/big_sticker/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🧩  квиз варианты',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/quiz_options/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='🗨  квиз впиши слово',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/quiz_input_word/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        c.Button(
            text='💬  квиз впиши фразу',
            on_click=GoToEvent(url=f'/slides/new/{lesson_id}/{source}/quiz_input_phrase/' + suffix),
            class_name='+ ms-2',
            named_style='secondary',
        ),
        c.Paragraph(text=''),
        back_button,
        title='Добавить новый слайд',
    )


@router.get('/new/{lesson_id}/{source}/{slide_type}/', response_model=FastUI, response_model_exclude_none=True)
async def create_slide_for_empty_path(
    lesson_id: int,
    source: SlidesMenuType,
    slide_type: SlideType,
    db_session: AsyncDBSession,
):
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    match slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            sticker_type = StickerType.SMALL if slide_type == SlideType.SMALL_STICKER else StickerType.BIG
            new_sticker_id = await create_new_sticker(lesson_id, sticker_type, db_session)
            await update_lesson_path(lesson_id, source, new_sticker_id, db_session)
            if source == SlidesMenuType.EXTRA:
                lesson.errors_threshold = ERRORS_THRESHOLD
            return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
        case _:
            form = get_new_slide_form_by_slide_type(slide_type, lesson_id, source)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title=f'Создание слайда | {slide_type.value}',
    )


@router.get('/new/{lesson_id}/{source}/{slide_type}/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def create_slide_for_existing_path(
    lesson_id: int,
    source: SlidesMenuType,
    slide_type: SlideType,
    index: int,
    db_session: AsyncDBSession,
):
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    match slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            sticker_type = StickerType.SMALL if slide_type == SlideType.SMALL_STICKER else StickerType.BIG
            new_sticker_id = await create_new_sticker(lesson_id, sticker_type, db_session)
            await update_lesson_path(lesson_id, source, new_sticker_id, db_session, index, PathType.EXISTING_PATH_NEW)
            return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson.id}/'))]
        case _:
            form = get_new_slide_form_by_slide_type(slide_type, lesson_id, source, index)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        form,
        title=f'Создание слайда | {slide_type.value}',
    )


@router.get('/edit/{source}/{slide_type}/{slide_id}/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def edit_slide(
    slide_id: int,
    source: SlidesMenuType,
    slide_type: SlideType,
    index: int,
    db_session: AsyncDBSession,
) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    optionnal_component = c.Paragraph(text='')
    match slide_type:
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            submit_url = f'/api/slides/edit/{source}/sticker/{slide_id}/{index}/'
            form = c.ModelForm(model=get_sticker_slide_data_model(slide), submit_url=submit_url)
        case SlideType.IMAGE:
            optionnal_component = c.Div(
                components=[
                    c.Image(
                        src=f'/static/lessons_images/{slide.lesson_id}/{slide.picture}',
                        width=IMAGE_WIDTH,
                        loading='lazy',
                        referrer_policy='no-referrer',
                    ),
                    c.Paragraph(text=''),
                ],
            )
            submit_url = f'/api/slides/edit/{source}/image/{slide_id}/{index}/'
            form = c.ModelForm(model=get_image_slide_data_model(slide), submit_url=submit_url)
        case _:
            form = get_edit_slide_form_by_slide_type(source, slide, index)
    return get_common_content(
        back_button,
        c.Paragraph(text=''),
        optionnal_component,
        c.Paragraph(text=''),
        form,
        title=f'Редактирование слайда {slide_id} | {slide.slide_type.value}',
    )


@router.get('/confirm_delete/{source}/{slide_id}/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def show_delete_slide_dialog(
    source: SlidesMenuType,
    slide_id: int,
    index: int,
    db_session: AsyncDBSession,
) -> list[AnyComponent]:
    slide: Slide = await get_slide_by_id(slide_id, db_session)
    logger.info(
        f'delete slide dialog called in lesson {slide.lesson_id}. ' f'slide_id: {slide_id}, index: {index}, source: {source}'
    )
    return get_common_content(
        c.Paragraph(text='Вы уверены, что хотите удалить слайд?'),
        c.Div(
            components=[
                back_button,
                c.Link(
                    components=[c.Button(text='Удалить', named_style='warning')],
                    on_click=GoToEvent(url=f'/slides/delete/{source}/{slide.lesson_id}/{index}/'),
                    class_name='+ ms-2',
                ),
            ],
        ),
        title=f'Удаление слайда {slide_id} | {slide.slide_type.value}',
    )


@router.get('/delete/{source}/{lesson_id}/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def confirm_delete_slide(
    source: SlidesMenuType,
    lesson_id: int,
    index: int,
    db_session: AsyncDBSession,
):
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    logger.info(f'deleting slide from lesson {lesson_id}. index: {index}, source: {source}')
    delete_slide(lesson, source, index)
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson_id}/'))]


@router.get('/{direction}/{source}/{lesson_id}/{index}/', response_model=FastUI, response_model_exclude_none=True)
async def move_slide_by_direction(
    direction: MoveSlideDirection,
    index: int,
    lesson_id: int,
    source: SlidesMenuType,
    db_session: AsyncDBSession,
) -> list[AnyComponent]:
    lesson: Lesson = await get_lesson_by_id(lesson_id, db_session)
    move_slide(lesson, source, direction, index)
    logger.info(f'moved slide {direction} in lesson: {lesson_id}. index: {index}. source: {source}')
    return [c.FireEvent(event=GoToEvent(url=f'/slides/lesson{lesson_id}/'))]
