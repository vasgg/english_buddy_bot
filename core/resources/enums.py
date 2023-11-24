from enum import Enum


class SlideType(Enum):
    INFO = 'info'
    QUIZ_OPTIONS = 'quiz_options'
    QUIZ_INPUT = 'quiz_input'


class LessonLevel(Enum):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
