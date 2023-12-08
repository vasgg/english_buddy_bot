import asyncio

from core.controllers.slide_controllers import get_slide_by_position
from core.database.db import db
from core.database.models import Slide
from core.resources.enums import KeyboardType, SlideType


async def add_new_slide_to_lesson(lesson_id: int, slide_type: SlideType, position: int,
                                  text: str = None, picture: str = None, delay: float = None,
                                  keyboard_type: KeyboardType = None, keyboard: str = None,
                                  right_answers: str = None, almost_right_answers: str = None,
                                  almost_right_answer_reply: str = None) -> None:
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
            )
        case SlideType.QUIZ_OPTIONS:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                keyboard_type=keyboard_type,
                keyboard=keyboard,
                right_answers=right_answers,
            )
        case SlideType.QUIZ_INPUT_WORD:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                right_answers=right_answers,
            )
        case SlideType.QUIZ_INPUT_PHRASE:
            new_slide = Slide(
                lesson_id=lesson_id,
                slide_type=slide_type,
                text=text,
                right_answers=right_answers,
                almost_right_answers=almost_right_answers,
                almost_right_answer_reply=almost_right_answer_reply,
            )
        case _:
            assert False, f'Unknown slide type: {slide_type}'

    async with db.session_factory.begin() as db_session:
        db_session.add(new_slide)
        await db_session.flush()
        old_slide_on_position = await get_slide_by_position(lesson_id=lesson_id, position=position, db_session=db_session)
        next_slide_id = old_slide_on_position.next_slide
        old_slide_on_position.next_slide = new_slide.id
        new_slide.next_slide = next_slide_id
        # TODO: при добавлении слайда с викториной инкрементить счётчик слайдов с викториной в таблице лессонс
        await db_session.commit()


if __name__ == '__main__':
    asyncio.run(add_new_slide_to_lesson(lesson_id=1, slide_type=SlideType.BIG_STICKER, position=85))
