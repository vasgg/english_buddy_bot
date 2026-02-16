from pydantic import BaseModel, ConfigDict


class SessionStatistics(BaseModel):
    all_sessions: dict
    completed: dict
    in_progress: dict
    aborted: dict


class SessionsStatisticsTableSchema(BaseModel):
    description: str
    value: int

    model_config = ConfigDict(from_attributes=True)


class SlidesStatistics(BaseModel):
    description: dict
    value: dict
    link: dict


class SlidesStatisticsTableSchema(BaseModel):
    slide_type: str
    is_exam_slide: str
    slide_id: str
    count_correct: str
    count_wrong: str
    lesson_title: str
    icon: str
    link: str
    correctness_rate: str

    model_config = ConfigDict(from_attributes=True)
