"""Task 1 API tests — no network, dependencies overridden with fakes."""
from fastapi.testclient import TestClient

from app.main import app, get_llm, get_retriever
from rag_core.grounding import INSUFFICIENT
from rag_core.testing import FakeLLM, make_sources


def _client(sources, reply="Thiazide diuretics are first-line [1]."):
    app.dependency_overrides[get_llm] = lambda: FakeLLM(reply=reply)
    app.dependency_overrides[get_retriever] = lambda: (lambda q, k: sources)
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_ask_grounded():
    client = _client(make_sources(("Thiazide diuretic is first-line.", 0.8)))
    r = client.post("/ask", json={"question": "first-line for hypertension?"})
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] is True
    assert "[1]" in body["answer"]


def test_ask_refuses_out_of_scope():
    client = _client(make_sources(("unrelated", 0.05)))
    r = client.post("/ask", json={"question": "capital of France?"})
    assert r.json()["answer"] == INSUFFICIENT
    assert r.json()["grounded"] is False


def test_empty_question_rejected():
    client = _client(make_sources(("x", 0.9)))
    r = client.post("/ask", json={"question": ""})
    assert r.status_code == 422
