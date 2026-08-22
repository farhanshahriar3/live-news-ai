import httpx
import pytest

from app.services.article_extractor import extract_article


@pytest.mark.asyncio
async def test_failed_extraction_returns_empty():
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    async with httpx.AsyncClient(transport=transport) as client:
        assert await extract_article("https://example.com", client=client) == ""


@pytest.mark.asyncio
async def test_extracts_paragraphs():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text="<script>x</script><p>Hello</p><p>World</p>")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        assert await extract_article("https://example.com", client=client) == "Hello World"
