from app.models.news import NewsArticle
from app.services.news_search import deduplicate_articles, normalize_url


def test_normalize_url_removes_tracking():
    assert normalize_url("https://Example.com/story/?utm_source=x") == "https://example.com/story"


def test_duplicate_articles_removed():
    articles = [
        NewsArticle(title="Same", url="https://example.com/a", source="A"),
        NewsArticle(title="Same", url="https://example.com/b", source="B"),
    ]
    assert len(deduplicate_articles(articles)) == 1
