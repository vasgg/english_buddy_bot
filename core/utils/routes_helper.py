import asyncio

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core.controllers.lesson_controllers import get_lesson
from core.controllers.slide_controllers import increment_lesson_slides_amount
from core.database.db import db
from core.database.models import Slide, SlideOrder
from core.resources.enums import KeyboardType, SlideType


async def routes_helper(lesson_number: int) -> None:
    async with db.session_factory.begin() as session:
        lesson = await get_lesson(lesson_number, session=session)
        slides_amount = lesson.slides_amount
        for i in range(1, slides_amount + 1):
            order_record = SlideOrder(lesson_id=lesson_number, slide_index=i, slide_id=i)
            session.add(order_record)
        await session.commit()


async def change_slides_order(lesson_id: int, slides_amount: int, position: int, session: AsyncSession) -> None:
    for i in range(position, slides_amount + 1):
        query = update(SlideOrder).filter(SlideOrder.lesson_id == lesson_id,
                                          SlideOrder.slide_index == i,
                                          SlideOrder.slide_id == i).values(slide_index=i + 1)
        await session.execute(query)


async def add_new_slide_to_lesson(lesson_id: int, slide_type: SlideType, position: int,
                                  text: str = None, picture: str = None, delay: float = None,
                                  keyboard_type: KeyboardType = None, keyboard: str = None,
                                  right_answers: str = None, almost_right_answers: str = None,
                                  right_answer_reply: str = None, almost_right_answer_reply: str = None,
                                  wrong_answer_reply: str = None) -> None:
    match slide_type:
        case SlideType.TEXT:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                delay=delay,
                keyboard_type=keyboard_type
            )
        case SlideType.IMAGE:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                picture=picture,
                delay=delay,
                keyboard_type=keyboard_type
            )
        case SlideType.SMALL_STICKER:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type
            )
        case SlideType.BIG_STICKER:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type
            )
        case SlideType.PIN_DICT:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                keyboard_type=keyboard_type
            )
        case SlideType.QUIZ_OPTIONS:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                keyboard_type=keyboard_type,
                keyboard=keyboard,
                right_answers=right_answers,
                right_answer_reply=right_answer_reply,
                wrong_answer_reply=wrong_answer_reply
            )
        case SlideType.QUIZ_INPUT_WORD:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                right_answers=right_answers,
                right_answer_reply=right_answer_reply,
                wrong_answer_reply=wrong_answer_reply
            )
        case SlideType.QUIZ_INPUT_PHRASE:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                right_answers=right_answers,
                almost_right_answers=almost_right_answers,
                right_answer_reply=right_answer_reply,
                almost_right_answer_reply=almost_right_answer_reply,
                wrong_answer_reply=wrong_answer_reply
            )
        case _:
            assert False, f'Unknown slide type: {slide_type}'
    async with db.session_factory.begin() as session:
        session.add(new_slide)
        await session.flush()
        new_slide_position = SlideOrder(lesson_id=lesson_id, slide_id=new_slide.id, slide_index=position)
        session.add(new_slide_position)
        await session.flush()
        lesson = await get_lesson(lesson_number=lesson_id, session=session)
        new_slides_amount = await increment_lesson_slides_amount(lesson_id=lesson_id, slides_amount=lesson.slides_amount, session=session)
        await change_slides_order(lesson_id=lesson_id, slides_amount=new_slides_amount, position=position, session=session)


if __name__ == '__main__':
    # asyncio.run(routes_helper(lesson_number=1))
    asyncio.run(add_new_slide_to_lesson(lesson_id=1, slide_type=SlideType.SMALL_STICKER, position=73))
