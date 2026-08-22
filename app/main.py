import logging
import time
from collections import defaultdict
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.graph.workflow import build_workflow
from app.llm import RequestGeminiModel, create_gemini
from app.models.chat import ChatRequest, ChatResponse
from app.services.news_search import NewsSearchService
from app.services.query_router import QueryType, answer_time, classify_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()
search_service = NewsSearchService(
    settings.tavily_api_key.get_secret_value() if settings.tavily_api_key else None,
    settings.max_search_results,
)
workflow = None
sessions: dict[str, list[dict[str, str]]] = defaultdict(list)

app = FastAPI(title="Live News AI", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "live-news-ai",
        "gemini_configured": settings.gemini_configured,
        "search_configured": settings.search_configured,
    }


@app.get("/api/news")
def news(query: str, time_range: str = "day") -> list[dict[str, object]]:
    """Expose a lightweight headline endpoint for integrations and debugging."""
    articles = search_service.search_news(query, time_range)
    return [article.model_dump(mode="json") for article in articles]


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    global workflow
    started = time.perf_counter()
    try:
        history = sessions[request.session_id][-10:]
        query_type = classify_query(request.message)
        gemini_calls = 0
        retrieved_sources = 0
        if query_type == QueryType.TIME:
            answer = ChatResponse(
                session_id=request.session_id,
                answer=answer_time(request.message, settings.app_timezone),
                sources=[],
                confidence="high",
                searched_at=datetime.now(UTC),
                query=request.message,
            )
        else:
            request_model = RequestGeminiModel(create_gemini(settings))
            workflow = build_workflow(request_model, search_service)
            result = workflow.invoke(
                {"message": request.message, "history": history, "query_type": query_type}
            )
            answer = ChatResponse(session_id=request.session_id, **result["answer"].model_dump())
            gemini_calls = request_model.calls
            retrieved_sources = len(answer.sources)
        logger.info(
            "query_type=%s gemini_calls=%d retrieved_sources=%d",
            query_type,
            gemini_calls,
            retrieved_sources,
        )
        sessions[request.session_id].extend(
            [
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": answer.answer},
            ]
        )
        logger.info("chat completed in %.2fs", time.perf_counter() - started)
        return answer
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("chat failed")
        error_message = str(exc)
        if settings.gemini_configured:
            error_message = error_message.replace(settings.require_gemini_key(), "[redacted]")
        lowered = error_message.lower()
        if (
            "incorrect api key" in lowered
            or "invalid_api_key" in lowered
            or "api key not valid" in lowered
        ):
            error_message = (
                "Gemini rejected GEMINI_API_KEY. Verify the key is active and copied exactly "
                "from Google AI Studio."
            )
        elif "authentication" in lowered and ("google" in lowered or "gemini" in lowered):
            error_message = (
                "Gemini authentication failed. Confirm GEMINI_API_KEY is set in .env and no stale "
                "environment variable is overriding it."
            )
        elif "resourceexhausted" in lowered or "quota" in lowered or "429" in lowered:
            error_message = (
                "Gemini's free-tier request quota has been reached. "
                "Please try again after the quota resets."
            )
        raise HTTPException(
            status_code=502,
            detail=f"{type(exc).__name__}: {error_message or 'unknown agent error'}",
        ) from exc


@app.delete("/api/session/{session_id}", status_code=204)
def delete_session(session_id: str) -> None:
    sessions.pop(session_id, None)
