from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser
import httpx

from app.models.news import NewsArticle

DEFAULT_FEEDS = {
    "Google News": "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
    "BBC": "https://feeds.bbci.co.uk/news/rss.xml",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
    "Guardian": "https://www.theguardian.com/world/rss",
}


def _published(entry: object) -> datetime | None:
    value = getattr(entry, "published", None)
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(UTC)
    except (TypeError, ValueError, OverflowError):
        return None


def search_rss(
    query: str, max_results: int = 8, feeds: dict[str, str] | None = None
) -> list[NewsArticle]:
    """Return matching headline entries from configured public RSS feeds."""
    terms = {term.lower() for term in query.split() if len(term) > 2}
    results: list[NewsArticle] = []
    configured_feeds = feeds or DEFAULT_FEEDS
    feed_items = [
        (source, feed_url.format(query=quote_plus(query)))
        for source, feed_url in configured_feeds.items()
    ]

    def fetch_feed(feed_item: tuple[str, str]) -> tuple[str, object]:
        source, feed_url = feed_item
        try:
            response = httpx.get(
                feed_url,
                timeout=5,
                follow_redirects=True,
                headers={"User-Agent": "LiveNewsAI/0.1"},
            )
            response.raise_for_status()
            return source, feedparser.parse(response.content)
        except (httpx.HTTPError, ValueError):
            return source, feedparser.FeedParserDict(entries=[])

    with ThreadPoolExecutor(max_workers=len(feed_items)) as executor:
        parsed_feeds = executor.map(fetch_feed, feed_items)

    for source, parsed in parsed_feeds:
        for entry in parsed.entries:
            text = f"{getattr(entry, 'title', '')} {getattr(entry, 'summary', '')}".lower()
            if terms and not any(term in text for term in terms):
                continue
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", None)
            if not url or not title:
                continue
            results.append(
                NewsArticle(
                    title=title,
                    url=url,
                    source=source,
                    published_at=_published(entry),
                    snippet=getattr(entry, "summary", ""),
                    query=query,
                )
            )
            if len(results) >= max_results:
                return results
    return results
