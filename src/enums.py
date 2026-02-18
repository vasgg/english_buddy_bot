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


class QuizType(StrEnum):
    REGULAR = auto()
    EXAM = auto()


class Stage(StrEnum):
    DEV = auto()
    PROD = auto()


class NotificationCampaignStatus(StrEnum):
    DRAFT = auto()
    ACTIVE = auto()
    PAUSED = auto()
    ARCHIVED = auto()


class NotificationSegmentMode(StrEnum):
    EXCLUDE = auto()
    INCLUDE = auto()


class NotificationDeliveryStatus(StrEnum):
    QUEUED = auto()
    SENT = auto()
    FAILED = auto()
    SKIPPED = auto()


class UserSubscriptionType(StrEnum):
    NO_ACCESS = auto()
    UNLIMITED_ACCESS = auto()
    LIMITED_ACCESS = auto()
    ACCESS_EXPIRED = auto()
    ACCESS_INFO_REQUESTED = auto()


class SubscriptionType(StrEnum):
    LIMITED = auto()
    ALLTIME = auto()


class SubscriptionDuration(StrEnum):
    ONE_MONTH = auto()
    THREE_MONTH = auto()


class SelectOneEnum(StrEnum):
    ALLTIME_ACCESS = auto()
    MONTHLY_ACCESS = auto()
    NO_ACCESS = auto()


class PathType(StrEnum):
    EXISTING_PATH_EDIT = auto()
    EXISTING_PATH_NEW = auto()


class LessonStatus(StrEnum):
    ACTIVE = auto()
    EDITING = auto()
    DISABLED = auto()


class MoveSlideDirection(StrEnum):
    UP = auto()
    DOWN = auto()


def sub_status_to_select_one(sub_status: UserSubscriptionType) -> SelectOneEnum:
    match sub_status:
        case UserSubscriptionType.UNLIMITED_ACCESS:
            return SelectOneEnum.ALLTIME_ACCESS
        case UserSubscriptionType.LIMITED_ACCESS:
            return SelectOneEnum.MONTHLY_ACCESS
        case UserSubscriptionType.NO_ACCESS:
            return SelectOneEnum.NO_ACCESS
        case UserSubscriptionType.ACCESS_INFO_REQUESTED:
            return SelectOneEnum.NO_ACCESS
        case UserSubscriptionType.ACCESS_INFO_REQUESTED:
            return SelectOneEnum.NO_ACCESS
        case _:
            assert False, f"Unexpected sub_status={sub_status!r}"


def lesson_to_session(lesson_starts_from: LessonStartsFrom) -> SessionStartsFrom:
    match lesson_starts_from:
        case LessonStartsFrom.BEGIN:
            return SessionStartsFrom.BEGIN
        case LessonStartsFrom.EXAM:
            return SessionStartsFrom.EXAM
        case _:
            msg = f"Unknown lesson_starts_from={lesson_starts_from!r}"
            raise AssertionError(msg)
