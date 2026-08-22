from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["service"] == "live-news-ai"


def test_empty_question_rejected():
    response = TestClient(app).post("/api/chat", json={"session_id": "s1", "message": " "})
    assert response.status_code == 422


def test_time_question_does_not_require_gemini_key(monkeypatch):
    monkeypatch.setattr("app.main.settings", app_settings_without_openai())
    response = TestClient(app).post(
        "/api/chat", json={"session_id": "s-time", "message": "What time is it in London?"}
    )
    assert response.status_code == 200
    assert response.json()["answer"].startswith("Current time in London:")
    assert response.json()["sources"] == []


def test_general_question_uses_one_gemini_call(monkeypatch):
    class FakeWorkflow:
        def invoke(self, state):
            return {"answer": type("Answer", (), {
                "model_dump": lambda self: {
                    "answer": "Dhaka.",
                    "sources": [],
                    "confidence": "medium",
                    "searched_at": "2026-08-22T00:00:00Z",
                    "query": state["message"],
                }
            })()}

    monkeypatch.setattr("app.main.workflow", FakeWorkflow())
    monkeypatch.setattr("app.main.create_gemini", lambda settings: type("Model", (), {
        "invoke": lambda self, messages: type("Response", (), {"content": "Dhaka."})()
    })())
    response = TestClient(app).post(
        "/api/chat",
        json={
            "session_id": "s-general",
            "message": "What is the capital of Bangladesh?",
        },
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Dhaka."


def test_chat_reports_missing_gemini_key_for_current_news(monkeypatch):
    monkeypatch.setattr("app.main.workflow", None)
    monkeypatch.setattr("app.main.settings", app_settings_without_openai())
    response = TestClient(app).post(
        "/api/chat",
        json={"session_id": "s2", "message": "What are the latest geopolitical developments?"},
    )
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def app_settings_without_openai():
    from app.config import Settings

    return Settings(_env_file=None)
