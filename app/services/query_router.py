import re
from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo


class QueryType(StrEnum):
    TIME = "time"
    CURRENT = "current"
    GENERAL = "general"


TIME_PATTERN = re.compile(r"\b(time|clock|timezone|date|today|tomorrow)\b", re.I)
CURRENT_TERMS = (
    "latest",
    "currently",
    "current",
    "right now",
    "recent",
    "this week",
    "this month",
    "breaking",
    "news",
    "happening",
    "development",
    "update",
    "war",
    "conflict",
    "election",
    "protest",
    "crisis",
    "president",
    "prime minister",
    "stock market",
    "weather",
    "gaza",
    "ukraine",
    "israel",
    "taiwan",
    "nato",
    "geopolitical",
)
HISTORICAL_TERMS = ("was the", "were the", "first", "former", "when did", "history")
TIMEZONES = {
    "bangladesh": ("Bangladesh", "Asia/Dhaka"),
    "dhaka": ("Dhaka", "Asia/Dhaka"),
    "london": ("London", "Europe/London"),
    "new york": ("New York", "America/New_York"),
    "los angeles": ("Los Angeles", "America/Los_Angeles"),
    "tokyo": ("Tokyo", "Asia/Tokyo"),
    "dubai": ("Dubai", "Asia/Dubai"),
    "singapore": ("Singapore", "Asia/Singapore"),
    "utc": ("UTC", "UTC"),
}


def classify_query(message: str) -> QueryType:
    text = " ".join(message.lower().split())
    if TIME_PATTERN.search(text) and any(
        term in text for term in ("time", "clock", "timezone", "date", "today", "tomorrow")
    ):
        return QueryType.TIME
    if any(term in text for term in HISTORICAL_TERMS):
        return QueryType.GENERAL
    if any(term in text for term in CURRENT_TERMS):
        return QueryType.CURRENT
    return QueryType.GENERAL


def answer_time(message: str, default_timezone: str = "UTC") -> str:
    text = message.lower()
    label, timezone_name = next(
        (value for key, value in TIMEZONES.items() if key in text),
        (default_timezone, default_timezone),
    )
    current = datetime.now(ZoneInfo(timezone_name))
    hour = current.strftime("%I").lstrip("0")
    return (
        f"Current time in {label}: {current.strftime('%A, %B')} {current.day}, "
        f"{current.year} at {hour}:{current:%M} {current:%p} {current:%Z}"
    )