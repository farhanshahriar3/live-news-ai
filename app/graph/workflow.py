from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.news_agent import evidence_text, make_answer, needs_live_search
from app.models.news import NewsAnswer, NewsArticle
from app.prompts.news_agent_prompt import SYSTEM_PROMPT
from app.services.query_router import QueryType

GENERAL_SYSTEM_PROMPT = """You are Live News AI, a concise and helpful assistant.
Answer general factual questions directly using your knowledge. Do not claim
that a general question requires live news retrieval. If the user asks for
current information, rely only on the supplied retrieved evidence.
Retrieved evidence follows:
{evidence}"""


class AgentState(TypedDict, total=False):
    message: str
    history: list[dict[str, str]]
    articles: list[NewsArticle]
    answer: NewsAnswer
    live: bool
    query_type: str


def build_workflow(model: Any, search_service: Any):
    def classify(state: AgentState) -> dict[str, Any]:
        query_type = state.get("query_type")
        if query_type:
            return {"live": query_type == QueryType.CURRENT}
        return {"live": needs_live_search(state["message"], state.get("history"))}

    def search(state: AgentState) -> dict[str, Any]:
        return {
            "articles": search_service.search_news(
                state["message"], "week" if "week" in state["message"].lower() else "day"
            )
        }

    def generate(state: AgentState) -> dict[str, Any]:
        evidence = evidence_text(state.get("articles", []))
        if state.get("live") and not evidence:
            return {
                "answer": make_answer(
                    "I could not retrieve reliable current news for this question, "
                    "so I will not guess.",
                    state["message"],
                    [],
                )
            }
        system_prompt = SYSTEM_PROMPT if state.get("live") else GENERAL_SYSTEM_PROMPT
        prompt = system_prompt.format(
            evidence=evidence or "No live search was needed; answer timelessly."
        )
        messages: list[tuple[str, str]] = [("system", prompt)]
        messages.extend(
            (item["role"], item["content"])
            for item in state.get("history", [])
            if item.get("role") in {"user", "assistant"} and item.get("content")
        )
        messages.append(("human", state["message"]))
        response = model.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        return {"answer": make_answer(content, state["message"], state.get("articles", []))}

    graph = StateGraph(AgentState)
    graph.add_node("classify", classify)
    graph.add_node("search", search)
    graph.add_node("generate", generate)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        lambda state: "search" if state["live"] else "generate",
        {"search": "search", "generate": "generate"},
    )
    graph.add_edge("search", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
