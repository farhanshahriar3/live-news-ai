from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from tavily import TavilyClient

from app.models.news import NewsArticle
from app.services.rss_news import search_rss


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, value) for key, value in parse_qsl(parts.query) if not key.lower().startswith("utm_")
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), "")
    )


def deduplicate_articles(articles: list[NewsArticle]) -> list[NewsArticle]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[NewsArticle] = []
    for article in articles:
        url_key = normalize_url(str(article.url))
        title_key = " ".join(article.title.lower().split())
        if url_key in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url_key)
        seen_titles.add(title_key)
        unique.append(article)
    return unique


class NewsSearchService:
    def __init__(self, tavily_api_key: str | None, max_results: int = 8) -> None:
        self.max_results = max_results
        self.client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

    def search_news(
        self, query: str, time_range: str = "day", max_results: int | None = None
    ) -> list[NewsArticle]:
        """Search current web news, degrading to RSS when the primary provider is unavailable."""
        limit = min(max_results or self.max_results, 5)
        articles: list[NewsArticle] = []
        if self.client:
            try:
                response = self.client.search(
                    query=query,
                    topic="news",
                    time_range=time_range,
                    max_results=limit,
                    include_raw_content=True,
                )
                for item in response.get("results", []):
                    if not item.get("url") or not item.get("title"):
                        continue
                    articles.append(
                        NewsArticle(
                            title=item["title"],
                            url=item["url"],
                            source=item.get("source") or item.get("url", "").split("/")[2],
                            snippet=item.get("content", ""),
                            content=item.get("raw_content", ""),
                            relevance_score=item.get("score"),
                            query=query,
                        )
                    )
            except Exception:
                articles = []
        if not articles:
            articles = search_rss(query, limit)
        return deduplicate_articles(articles)[:limit]
