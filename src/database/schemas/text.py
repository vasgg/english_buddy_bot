from pydantic import BaseModel, Field


class TextsSchema(BaseModel):
    id: int = Field(title=' ')
    description: str | None = Field(title='description')
    text: str | None = Field(title='text')

    class Config:
        from_attributes = True
        extra = 'allow'


class TextsTableSchema(TextsSchema):
    edit_button: str = Field("✏️", title=" ")
    minus_button: str = Field("➖", title=" ")

    class Config:
        from_attributes = True
