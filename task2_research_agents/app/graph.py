"""LangGraph wiring of the three agents (Research -> Summarize -> Report).

Imported lazily so the app/tests don't hard-require langgraph unless the graph is used.
"""
from __future__ import annotations

from functools import partial

from .agents import report_agent, research_agent, summarizer_agent
from .state import ResearchState


def build_graph(llm, retrieve_fn):
    from langgraph.graph import END, START, StateGraph

    g = StateGraph(ResearchState)
    g.add_node("research", partial(research_agent, llm=llm, retrieve_fn=retrieve_fn))
    g.add_node("summarize", partial(summarizer_agent, llm=llm))
    g.add_node("report", partial(report_agent, llm=llm))

    g.add_edge(START, "research")
    g.add_edge("research", "summarize")
    g.add_edge("summarize", "report")
    g.add_edge("report", END)
    return g.compile()


def run_graph(topic: str, llm, retrieve_fn, mode: str = "corpus") -> ResearchState:
    app = build_graph(llm, retrieve_fn)
    return app.invoke({"topic": topic, "mode": mode, "errors": []})
