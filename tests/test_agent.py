from app.agents.news_agent import needs_live_search
from app.graph.workflow import build_workflow
from app.llm import RequestGeminiModel


def test_current_question_requires_search():
    assert needs_live_search("What happened in Bangladesh today?")


def test_timeless_question_does_not_require_search():
    assert not needs_live_search("What is a parliamentary system?")


def test_workflow_preserves_previous_messages():
    calls = []

    class FakeModel:
        def invoke(self, messages):
            calls.append(messages)
            return type("Response", (), {"content": "Answer"})()

    workflow = build_workflow(FakeModel(), type("Search", (), {"search_news": lambda *args: []})())
    workflow.invoke({"message": "My name is Farhan.", "history": []})
    workflow.invoke(
        {
            "message": "Could you tell me my name from our earlier conversation?",
            "history": [
                {"role": "user", "content": "My name is Farhan."},
                {"role": "assistant", "content": "Answer"},
            ],
        }
    )

    assert ("user", "My name is Farhan.") in calls[1]
    assert ("assistant", "Answer") in calls[1]


def test_gemini_request_guard_allows_one_call():
    class FakeModel:
        def invoke(self, messages):
            return type("Response", (), {"content": "Answer"})()

    model = RequestGeminiModel(FakeModel())
    model.invoke("first")

    try:
        model.invoke("second")
    except RuntimeError as error:
        assert "limit reached" in str(error)
    else:
        raise AssertionError("A second Gemini call was allowed")

    assert model.calls == 1
