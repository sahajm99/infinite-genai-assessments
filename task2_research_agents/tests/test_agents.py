"""Task 2 tests — agents and sequential orchestration, no network/langgraph."""
from app.agents import report_agent, research_agent, run_pipeline, summarizer_agent
from app.state import Report
from rag_core.testing import make_sources


class ScriptedLLM:
    """Routes JSON responses by system-prompt content; plain replies for complete()."""

    def complete(self, messages, temperature: float = 0.2, **kw):
        return "A concise grounded finding."

    def complete_json(self, messages, temperature: float = 0.0):
        system = messages[0]["content"].lower()
        if "sub-question" in system or "research planner" in system:
            return {"subquestions": ["What are agents?", "What are the risks?"]}
        return {
            "executive_summary": "Agents are powerful but risky.",
            "key_findings": ["Compounding errors", "Framework helps"],
            "risks": ["Prompt injection"],
            "recommendations": ["Add guardrails"],
        }


def _retrieve(_q):
    return make_sources(("Agents couple an LLM with tools and memory.", 0.7))


def test_research_agent_produces_findings():
    out = research_agent({"topic": "LLM agents"}, ScriptedLLM(), _retrieve)
    assert len(out["subquestions"]) == 2
    assert len(out["findings"]) == 2
    assert out["findings"][0].sources == ["test"]


def test_summarizer_produces_summary():
    state = research_agent({"topic": "LLM agents"}, ScriptedLLM(), _retrieve)
    out = summarizer_agent({**state}, ScriptedLLM())
    assert out["summary"]


def test_full_pipeline_yields_complete_report():
    state = run_pipeline("LLM agents in production", ScriptedLLM(), _retrieve)
    report: Report = state["report"]
    assert report.executive_summary
    assert report.key_findings and report.risks and report.recommendations


def test_bad_retrieval_does_not_crash_pipeline():
    def boom(_q):
        raise RuntimeError("vector store down")

    state = run_pipeline("topic", ScriptedLLM(), boom)
    # Still produces a report; error recorded.
    assert isinstance(state["report"], Report)
    assert any("finding failed" in e for e in state["errors"])
