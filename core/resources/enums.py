from enum import Enum

from aiogram.filters.state import State, StatesGroup


class States(StatesGroup):
    INPUT_WORD = State()
    INPUT_PHRASE = State()


class SlideType(Enum):
    TEXT = 'text'
    IMAGE = 'image'
    STICKER = 'sticker'
    QUIZ_OPTIONS = 'quiz_options'
    QUIZ_INPUT_WORD = 'quiz_input_word'
    QUIZ_INPUT_PHRASE = 'quiz_input_phrase'


class LessonLevel(Enum):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'


class KeyboardType(Enum):
    FURTHER = 'further'
    QUIZ = 'quiz'
