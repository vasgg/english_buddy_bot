from pydantic import BaseModel


class UserInputMsg(BaseModel):
    text: str


class UserInputHint(BaseModel):
    hint_requested: bool


UserQuizInput = UserInputMsg | UserInputHint
