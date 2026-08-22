from typing import Any

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import Settings


class _RetryCompatibleClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    def generate_content(self, **kwargs: Any) -> Any:
        kwargs.pop("max_retries", None)
        return self._client.generate_content(**kwargs)

    def stream_generate_content(self, **kwargs: Any) -> Any:
        kwargs.pop("max_retries", None)
        return self._client.stream_generate_content(**kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class GeminiModel:
    """Small adapter around LangChain's Gemini chat model."""

    def __init__(self, settings: Settings) -> None:
        self.client = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.require_gemini_key(),
            temperature=0.1,
            retries=0,
            request_timeout=20,
        )
        self.client.client = _RetryCompatibleClient(self.client.client)

    def invoke(self, messages: str | list[Any]) -> AIMessage:
        return self.client.invoke(messages)


class RequestGeminiModel:
    """Request-scoped guard that prevents accidental duplicate Gemini calls."""

    def __init__(self, model: GeminiModel, max_calls: int = 1) -> None:
        self.model = model
        self.max_calls = max_calls
        self.calls = 0

    def invoke(self, messages: str | list[Any]) -> AIMessage:
        if self.calls >= self.max_calls:
            raise RuntimeError("Gemini call limit reached for this request.")
        self.calls += 1
        return self.model.invoke(messages)


def create_gemini(settings: Settings) -> GeminiModel:
    """Create the Gemini model after validating the configured key."""
    return GeminiModel(settings)


create_openai = create_gemini
