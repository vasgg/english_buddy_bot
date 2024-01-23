from enum import Enum

from aiogram.filters.state import State, StatesGroup


class States(StatesGroup):
    INPUT_WORD = State()
    INPUT_PHRASE = State()
    INPUT_CUSTOM_SLIDE_ID = State()


class SlideType(Enum):
    TEXT = 'text'
    IMAGE = 'image'
    SMALL_STICKER = 'small_sticker'
    BIG_STICKER = 'big_sticker'
    PIN_DICT = 'pin_dict'
    QUIZ_OPTIONS = 'quiz_options'
    QUIZ_INPUT_WORD = 'quiz_input_word'
    QUIZ_INPUT_PHRASE = 'quiz_input_phrase'
    FINAL_SLIDE = 'final_slide'


class LessonLevel(Enum):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'


class KeyboardType(Enum):
    FURTHER = 'further'
    QUIZ = 'quiz'


class UserLessonProgress(Enum):
    NO_PROGRESS = 'no_progress'
    IN_PROGRESS = 'in_progress'


class SessionStartsFrom(Enum):
    BEGIN = 'begin'
    EXAM = 'exam'


class ReactionType(Enum):
    RIGHT = 'right'
    WRONG = 'wrong'


class StickerType(Enum):
    BIG = 'big'
    SMALL = 'small'


class SessionStatus(Enum):
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ABORTED = 'aborted'


class LessonStartsFrom(Enum):
    BEGIN = 'begin'
    EXAM = 'exam'
    CONTINUE = 'continue'


class EventType(Enum):
    MESSAGE = 'message'
    CALLBACK_QUERY = 'callback_query'
    HINT = 'hint'
    CONTINUE = 'continue'


class Times(Enum):
    UTC_STARTING_MARK = 14
    ONE_HOUR = 3600


def lesson_to_session(lesson_starts_from: LessonStartsFrom) -> SessionStartsFrom:
    match lesson_starts_from:
        case LessonStartsFrom.BEGIN:
            return SessionStartsFrom.BEGIN
        case LessonStartsFrom.EXAM:
            return SessionStartsFrom.EXAM
        case _:
            assert False, f'Unknown {lesson_starts_from=}'
