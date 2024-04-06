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
    slide_id: int
    lesson_title: str
    value: int
    link: str
    icon: str

    model_config = ConfigDict(from_attributes=True)
