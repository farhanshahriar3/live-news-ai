from datetime import UTC, datetime

from app.models.news import NewsAnswer, NewsArticle, Source

LIVE_TERMS = (
    "latest",
    "today",
    "right now",
    "currently",
    "breaking",
    "this week",
    "yesterday",
    "recent",
    "last 24",
    "this morning",
)


def needs_live_search(message: str, history: list[dict[str, str]] | None = None) -> bool:
    text = message.lower()
    return any(term in text for term in LIVE_TERMS) or bool(
        history and len(history) > 0 and len(text.split()) < 8
    )


def evidence_text(articles: list[NewsArticle]) -> str:
    return "\n".join(
        f"[{index}] {a.source}: {a.title}\n{(a.snippet or a.content)[:1600]}\nURL: {a.url}"
        for index, a in enumerate(articles, 1)
    )


def make_answer(text: str, query: str, articles: list[NewsArticle]) -> NewsAnswer:
    sources = [
        Source(
            title=a.title,
            url=a.url,
            source_name=a.source,
            published_at=a.published_at,
            relevance_score=a.relevance_score,
        )
        for a in articles
    ]
    confidence = (
        "high" if len({a.source for a in articles}) >= 2 else "medium" if articles else "low"
    )
    return NewsAnswer(
        answer=text,
        sources=sources,
        confidence=confidence,
        searched_at=datetime.now(UTC),
        query=query,
    )
