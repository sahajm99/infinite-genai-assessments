"""Task 3 tests — escalation + memory, no network."""
from fastapi.testclient import TestClient

from app.main import app, get_llm, get_retriever
from rag_core.testing import FakeLLM, make_sources


def _client(sources, reply="The Team plan allows 600 requests per minute [1]."):
    app.dependency_overrides[get_llm] = lambda: FakeLLM(reply=reply)
    app.dependency_overrides[get_retriever] = lambda: (lambda q, k: sources)
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_confident_answer_no_escalation():
    client = _client(make_sources(("Team plan: 600 rpm.", 0.78)))
    r = client.post("/chat", json={"session_id": "s1", "message": "team rate limit?"})
    body = r.json()
    assert body["escalate"] is False
    assert "[1]" in body["answer"]


def test_low_confidence_escalates():
    client = _client(make_sources(("barely related", 0.10)))
    r = client.post("/chat", json={"session_id": "s2", "message": "do you integrate with SAP?"})
    body = r.json()
    assert body["escalate"] is True
    assert "human support agent" in body["answer"]


def test_missing_session_id_rejected():
    client = _client(make_sources(("x", 0.9)))
    r = client.post("/chat", json={"message": "hi"})
    assert r.status_code == 422


def test_memory_persists_across_turns():
    client = _client(make_sources(("Annual billing gives 20% discount.", 0.7)))
    client.post("/chat", json={"session_id": "s3", "message": "how much is the Team plan?"})
    client.post("/chat", json={"session_id": "s3", "message": "and annually?"})
    hist = client.get("/session/s3").json()
    assert len(hist["turns"]) == 4  # 2 user + 2 assistant
