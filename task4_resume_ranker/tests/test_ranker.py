"""Task 4 tests — parsing, scoring, ranking with fakes (no network)."""
from fastapi.testclient import TestClient

from app.main import app, get_embedder_dep, get_llm
from app.scorer import score_candidate
from app.models import CandidateProfile
from rag_core.testing import FakeEmbedder


class ScriptedLLM:
    """Returns an extraction profile then a rubric score, keyed by prompt content."""

    def __init__(self, rubric_score, strengths=None, gaps=None):
        self.rubric_score = rubric_score
        self.strengths = strengths or []
        self.gaps = gaps or []

    def complete_json(self, messages, temperature: float = 0.0):
        system = messages[0]["content"]
        if "extract structured data" in system.lower():
            return {"name": "Test", "skills": ["Python"], "education": [],
                    "experience": [], "certifications": [], "total_years": 5}
        return {"rubric_score": self.rubric_score, "strengths": self.strengths,
                "gaps": self.gaps, "justification": "ok"}


def test_scorer_combines_semantic_and_rubric():
    prof = CandidateProfile(name="A", skills=["Python"], total_years=6)
    rc = score_candidate("c1", prof, "python fastapi aws postgres", "python backend aws",
                         ScriptedLLM(90), FakeEmbedder())
    # combined = 0.4*sem*100 + 0.6*90 ; rubric contributes 54
    assert rc.rubric_score == 90.0
    assert rc.score >= 54.0
    assert 0.0 <= rc.semantic_score <= 1.0


def _client(rubric_score):
    app.dependency_overrides[get_llm] = lambda: ScriptedLLM(rubric_score)
    app.dependency_overrides[get_embedder_dep] = lambda: FakeEmbedder()
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_rank_endpoint_sorts_desc():
    # Strong candidate scored 95, weak scored 20 -> strong must rank first.
    app.dependency_overrides[get_embedder_dep] = lambda: FakeEmbedder()

    class TwoTier:
        def complete_json(self, messages, temperature: float = 0.0):
            content = messages[-1]["content"]
            if "extract structured data" in messages[0]["content"].lower():
                return {"name": "X", "skills": [], "education": [], "experience": [],
                        "certifications": [], "total_years": 1}
            score = 95 if "STRONG" in content else 20
            return {"rubric_score": score, "strengths": [], "gaps": [], "justification": ""}

    app.dependency_overrides[get_llm] = lambda: TwoTier()
    client = TestClient(app)
    r = client.post("/rank", json={
        "job_description": "python backend",
        "resumes": [
            {"id": "weak", "text": "this is a WEAK unrelated frontend resume text here"},
            {"id": "strong", "text": "this is a STRONG python backend aws resume text here"},
        ],
    })
    ranked = r.json()["ranked"]
    assert ranked[0]["id"] == "strong"
    assert ranked[0]["score"] > ranked[1]["score"]


def test_empty_resumes_rejected():
    client = _client(50)
    r = client.post("/rank", json={"job_description": "x", "resumes": []})
    assert r.status_code == 422


def test_unparseable_resume_skipped_not_fatal():
    client = _client(80)
    r = client.post("/rank", json={
        "job_description": "python backend",
        "resumes": [{"id": "empty", "text": "  "}],
    })
    body = r.json()
    assert body["ranked"] == []
    assert body["skipped"][0]["id"] == "empty"
