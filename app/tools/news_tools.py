from datetime import UTC, datetime

from langchain_core.tools import tool

from app.services.news_search import NewsSearchService


def build_news_tools(service: NewsSearchService):
    @tool
    def search_news(query: str, time_range: str = "day") -> str:
        """Search fresh news and return structured article evidence."""
        articles = service.search_news(query, time_range)
        return "\n".join(f"{a.source} | {a.title} | {a.url} | {a.snippet}" for a in articles)

    @tool
    def get_current_time() -> str:
        """Return the current UTC time for interpreting relative dates."""
        return datetime.now(UTC).isoformat()

    return [search_news, get_current_time]
