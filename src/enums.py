from enum import StrEnum, auto

from aiogram.filters.state import State, StatesGroup


class States(StatesGroup):
    INPUT_WORD = State()
    INPUT_PHRASE = State()
    INPUT_CUSTOM_SLIDE_ID = State()


class SlideType(StrEnum):
    TEXT = auto()
    IMAGE = auto()
    SMALL_STICKER = auto()
    BIG_STICKER = auto()
    PIN_DICT = auto()
    QUIZ_OPTIONS = auto()
    QUIZ_INPUT_WORD = auto()
    QUIZ_INPUT_PHRASE = auto()


class LessonLevel(StrEnum):
    BEGINNER = auto()
    INTERMEDIATE = auto()
    ADVANCED = auto()


class KeyboardType(StrEnum):
    FURTHER = auto()
    QUIZ = auto()


class UserLessonProgress(StrEnum):
    NO_PROGRESS = auto()
    IN_PROGRESS = auto()


class SessionStartsFrom(StrEnum):
    BEGIN = auto()
    EXAM = auto()


class ReactionType(StrEnum):
    RIGHT = auto()
    WRONG = auto()


class StickerType(StrEnum):
    BIG = auto()
    SMALL = auto()


class SessionStatus(StrEnum):
    IN_PROGRESS = auto()
    COMPLETED = auto()
    ABORTED = auto()


class LessonStartsFrom(StrEnum):
    BEGIN = auto()
    EXAM = auto()
    CONTINUE = auto()


class EventType(StrEnum):
    MESSAGE = auto()
    CALLBACK_QUERY = auto()
    HINT = auto()
    CONTINUE = auto()


class SlidesMenuType(StrEnum):
    REGULAR = auto()
    EXTRA = auto()


def lesson_to_session(lesson_starts_from: LessonStartsFrom) -> SessionStartsFrom:
    match lesson_starts_from:
        case LessonStartsFrom.BEGIN:
            return SessionStartsFrom.BEGIN
        case LessonStartsFrom.EXAM:
            return SessionStartsFrom.EXAM
        case _:
            msg = f'Unknown lesson_starts_from={lesson_starts_from!r}'
            raise AssertionError(msg)
