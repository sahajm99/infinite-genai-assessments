"""The three agents as pure, independently testable functions.

Each takes the current state plus injected dependencies (llm, retrieve_fn) and
returns a partial state update. No agent calls another — orchestration lives in graph.py.
"""
from __future__ import annotations

from . import prompts
from .state import Finding, Report, ResearchState


def research_agent(state: ResearchState, llm, retrieve_fn) -> ResearchState:
    """Decompose the topic and gather a grounded finding per sub-question."""
    topic = state["topic"]
    errors: list[str] = []
    try:
        plan = llm.complete_json([
            {"role": "system", "content": prompts.SUBQUESTIONS_SYSTEM},
            {"role": "user", "content": f"Topic: {topic}"},
        ])
        subqs = plan.get("subquestions", [])[:5] or [topic]
    except Exception as exc:  # noqa: BLE001
        errors.append(f"planning failed: {exc}")
        subqs = [topic]

    findings: list[Finding] = []
    for q in subqs:
        try:
            sources = retrieve_fn(q)
            context = "\n\n".join(s.text for s in sources) or "(no context found)"
            content = llm.complete([
                {"role": "system", "content": prompts.FINDING_SYSTEM},
                {"role": "user", "content": f"Sub-question: {q}\n\nContext:\n{context}"},
            ])
            findings.append(Finding(
                question=q, content=content.strip(),
                sources=[s.metadata.get("source", "unknown") for s in sources],
            ))
        except Exception as exc:  # noqa: BLE001 - one bad sub-question doesn't sink the run
            errors.append(f"finding failed for '{q}': {exc}")

    return {"subquestions": subqs, "findings": findings, "errors": errors}


def summarizer_agent(state: ResearchState, llm) -> ResearchState:
    findings = state.get("findings", [])
    joined = "\n".join(f"- {f.question}: {f.content}" for f in findings) or "(none)"
    try:
        summary = llm.complete([
            {"role": "system", "content": prompts.SUMMARY_SYSTEM},
            {"role": "user", "content": f"Findings:\n{joined}"},
        ]).strip()
    except Exception as exc:  # noqa: BLE001
        return {"summary": "", "errors": state.get("errors", []) + [f"summary failed: {exc}"]}
    return {"summary": summary}


def report_agent(state: ResearchState, llm) -> ResearchState:
    findings = state.get("findings", [])
    joined = "\n".join(f"- {f.question}: {f.content}" for f in findings) or "(none)"
    try:
        data = llm.complete_json([
            {"role": "system", "content": prompts.REPORT_SYSTEM},
            {"role": "user", "content": (
                f"Topic: {state['topic']}\n\nSummary: {state.get('summary','')}\n\n"
                f"Findings:\n{joined}"
            )},
        ])
        report = Report.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        report = Report(executive_summary=state.get("summary", ""),
                        key_findings=[f.content for f in findings])
        return {"report": report, "errors": state.get("errors", []) + [f"report failed: {exc}"]}
    return {"report": report}


def run_pipeline(topic: str, llm, retrieve_fn, mode: str = "corpus") -> ResearchState:
    """Sequential orchestration (used by tests and as a no-langgraph fallback)."""
    state: ResearchState = {"topic": topic, "mode": mode, "errors": []}
    state.update(research_agent(state, llm, retrieve_fn))
    state.update(summarizer_agent(state, llm))
    state.update(report_agent(state, llm))
    return state
