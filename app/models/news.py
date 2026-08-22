from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class NewsArticle(BaseModel):
    title: str = Field(min_length=1)
    url: HttpUrl
    source: str = "Unknown source"
    published_at: datetime | None = None
    snippet: str = ""
    content: str = ""
    image_url: HttpUrl | None = None
    relevance_score: float | None = None
    query: str = ""

    @property
    def citation_label(self) -> str:
        return f"{self.source} - {self.title}"


class Source(BaseModel):
    title: str
    url: HttpUrl
    source_name: str
    published_at: datetime | None = None
    relevance_score: float | None = None


class NewsAnswer(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    confidence: str = "medium"
    searched_at: datetime
    query: str
