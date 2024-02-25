from pydantic import BaseModel, Field


class ReactionsSchema(BaseModel):
    id: int = Field(title='id')
    text: str | None = Field(title='text')

    class Config:
        from_attributes = True
        extra = 'allow'


class ReactionsTableSchema(ReactionsSchema):
    edit_button: str = Field("✏️", title=" ")
    minus_button: str = Field("➖", title=" ")

    class Config:
        from_attributes = True


class DeleteReaction(BaseModel):
    id: int = Field(title='id')

    class Config:
        from_attributes = True
