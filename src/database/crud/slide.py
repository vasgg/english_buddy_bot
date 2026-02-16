from database.models.slide import Slide
from enums import QuizType, SlideType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_slide_by_id(slide_id: int, db_session: AsyncSession) -> Slide | None:
    query = select(Slide).filter(Slide.id == slide_id)
    result = await db_session.execute(query)
    slide = result.scalar()
    return slide


async def get_slides_by_ids(slide_ids: list[int], db_session: AsyncSession) -> dict[int, Slide]:
    if not slide_ids:
        return {}
    query = select(Slide).where(Slide.id.in_(slide_ids))
    result = await db_session.execute(query)
    slides = result.scalars().all()
    return {slide.id: slide for slide in slides}


async def find_first_exam_slide_id(slide_ids: list[int], db_session: AsyncSession) -> int | None:
    for slide_id in slide_ids:
        slide = await get_slide_by_id(slide_id, db_session)
        if slide and slide.is_exam_slide:
            return slide_id
    return None


async def get_quiz_slides_by_mode(slides_ids: list[int], mode: QuizType, db_session: AsyncSession) -> set[int]:
    all_questions_slide_types = [SlideType.QUIZ_OPTIONS, SlideType.QUIZ_INPUT_WORD, SlideType.QUIZ_INPUT_PHRASE]
    query = select(Slide.id).filter(
        Slide.id.in_(slides_ids),
        Slide.slide_type.in_(all_questions_slide_types),
        ~Slide.is_exam_slide if mode == QuizType.REGULAR else Slide.is_exam_slide,
    )
    result = await db_session.execute(query)
    return set(result.scalars().all())
