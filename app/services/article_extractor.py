import httpx
from bs4 import BeautifulSoup


async def extract_article(
    url: str, max_chars: int = 12000, client: httpx.AsyncClient | None = None
) -> str:
    """Extract readable paragraph text, returning an empty string on fetch failure."""
    owns_client = client is None
    http_client = client or httpx.AsyncClient(
        timeout=8, follow_redirects=True, headers={"User-Agent": "LiveNewsAI/0.1"}
    )
    try:
        response = await http_client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        text = " ".join(paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p"))
        return " ".join(text.split())[:max_chars]
    except (httpx.HTTPError, ValueError):
        return ""
    finally:
        if owns_client:
            await http_client.aclose()
