"""Core grounding behavior — no network required."""
from rag_core.grounding import INSUFFICIENT, answer_from_context
from rag_core.testing import FakeLLM, make_sources


def test_refuses_when_no_sources():
    ans = answer_from_context("q", [], FakeLLM(), threshold=0.35)
    assert ans.grounded is False
    assert ans.answer == INSUFFICIENT


def test_refuses_when_below_threshold():
    sources = make_sources(("weakly related text", 0.10))
    llm = FakeLLM(reply="should not be called")
    ans = answer_from_context("q", sources, llm, threshold=0.35)
    assert ans.grounded is False
    assert ans.answer == INSUFFICIENT
    assert llm.calls == []  # guarded before spending a token


def test_answers_and_cites_with_good_context():
    sources = make_sources(("Aspirin reduces clotting.", 0.82))
    llm = FakeLLM(reply="Aspirin reduces clotting [1].")
    ans = answer_from_context("what does aspirin do?", sources, llm, threshold=0.35)
    assert ans.grounded is True
    assert "[1]" in ans.answer
    assert ans.sources[0].score == 0.82


def test_detects_model_refusal_as_ungrounded():
    sources = make_sources(("irrelevant but high score", 0.9))
    llm = FakeLLM(reply=INSUFFICIENT)
    ans = answer_from_context("q", sources, llm, threshold=0.35)
    assert ans.grounded is False
