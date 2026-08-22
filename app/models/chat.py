from pydantic import BaseModel, Field, field_validator

from app.models.news import NewsAnswer


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("session_id", "message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank")
        return value.strip()


class ChatResponse(NewsAnswer):
    session_id: str
