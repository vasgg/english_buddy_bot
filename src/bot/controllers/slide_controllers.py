import logging
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.lesson import Lesson
from database.models.slide import Slide
from enums import KeyboardType, SlideType

logger = logging.Logger(__name__)


async def get_all_base_questions_id_in_lesson(
    lesson_id: int, exam_slides_id: set[int], db_session: AsyncSession
) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.lesson_id == lesson_id, Slide.slide_type.in_(all_questions_slide_types), ~Slide.id.in_(exam_slides_id)
    )
    result = await db_session.execute(query)
    return {row for row in result.scalars().all()} if result else {}


async def get_steps_to_current_slide(first_slide_id: int, target_slide_id: int, path: str) -> int:
    slide_ids_str = path.split(".")
    slide_ids = [int(id_str) for id_str in slide_ids_str]
    start_index = slide_ids.index(first_slide_id)
    target_index = slide_ids.index(target_slide_id)
    steps = abs(target_index - start_index)
    return steps


async def set_new_slide_image(slide_id: int, image_name: str, db_session: AsyncSession):
    stmt = select(Slide).filter(Slide.id == slide_id)
    result = await db_session.execute(stmt)
    slide = result.scalar_one()
    slide.picture = image_name
    await db_session.commit()


async def get_all_slides_from_lesson_by_order(lesson_id, db_session) -> list[Slide]:
    slides_query = await db_session.execute(select(Slide).where(Slide.lesson_id == lesson_id))
    slides = slides_query.scalars().all()
    slides_dict = {slide.id: slide for slide in slides}
    ordered_slides = []
    first_slide_query = await db_session.execute(select(Lesson.first_slide_id).where(Lesson.id == lesson_id))
    current_slide = first_slide_query.scalar()
    while current_slide:
        current_slide = slides_dict.get(current_slide)
        if current_slide:
            ordered_slides.append(current_slide)
            current_slide = current_slide.next_slide
        else:
            break
    return ordered_slides


def get_image_files_list(lesson_id: int) -> list[str]:
    directory = f'src/webapp/static/lessons_images/{lesson_id}'
    allowed_image_formats = ['png', 'jpg', 'jpeg', 'gif', 'heic', 'tiff', 'webp']
    files = []
    for filename in os.listdir(directory):
        if filename.rsplit('.', 1)[1].lower() in allowed_image_formats:
            files.append(filename)
    return files


def add_new_slide(lesson_id: int, slide_type: SlideType, slide_id: int | None = None):
    match slide_type:
        case SlideType.TEXT | SlideType.PIN_DICT | SlideType.FINAL_SLIDE:
            slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=f"New {slide_type} slide template",
                next_slide=slide_id,
            )
        case SlideType.IMAGE:
            slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                picture='src/webapp/static/lessons_images/image_not_available.png',
                next_slide=slide_id,
            )
        case SlideType.SMALL_STICKER | SlideType.BIG_STICKER:
            slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                next_slide=slide_id,
            )
        case SlideType.QUIZ_OPTIONS:
            slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                keyboard_type=KeyboardType.QUIZ,
                keyboard='вариант1|вариант2|вариант3',
                text=f"New {slide_type} slide template. Варианты ответов разделяются '|', заполните строку вариантов ответов"
                f" возможными вариантами. Убедитесь, что в поле ОТВЕТ есть один из вариантов ответа",
                right_answers='вариант3',
                next_slide=slide_id,
            )
        case SlideType.QUIZ_INPUT_WORD:
            slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=f"New {slide_type} slide template. Здесь нужен текст фразы с пропущенным словом (символ …). ",
                right_answers='тут нужен правильный ответ (он будет подставлен вместо … при правильном вводе',
                next_slide=slide_id,
            )
        case SlideType.QUIZ_INPUT_PHRASE:
            slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=f"New {slide_type} slide template. Здесь нужен текст фразы для перевода на английский язык. ",
                right_answers='тут нужен правильный ответ. Если их несколько, пишем несколько вариантов через "|".',
                almost_right_answers='тут будут почти правильные ответы. Если их несколько, пишем несколько вариантов через "|".',
                almost_right_answer_reply='тут вставляем пояснение на "почти правильный ответ"',
                next_slide=slide_id,
            )
        case _:
            assert False, f'Unknown slide type: {slide_type}'
    return slide
