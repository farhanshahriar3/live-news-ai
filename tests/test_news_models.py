import pytest
from pydantic import ValidationError

from app.models.news import NewsArticle


def test_article_requires_url():
    with pytest.raises(ValidationError):
        NewsArticle(title="Headline", url="not-a-url")


def test_article_model():
    article = NewsArticle(title="Headline", url="https://example.com/story", source="Example")
    assert article.citation_label == "Example - Headline"
