# Task 4 — AI Resume Screening & Candidate Ranking

Ranks resumes against a job description and returns each candidate with a hybrid score,
strengths, and gaps. Pipeline: **parse → extract (LLM, structured JSON) → score (hybrid)
→ rank**.

## Scoring formula (hybrid — bonus)
```
score = 0.4 * semantic_similarity(resume, JD) * 100  +  0.6 * rubric_score
```
- `semantic_similarity` = cosine of OpenAI embeddings of the resume vs the JD.
- `rubric_score` = LLM (0–100) judging skill coverage, seniority match, domain relevance.
Extraction and scoring run at `temperature=0` for consistent, repeatable rankings.

## Run it

### Docker (recommended)
```bash
# from repo root
cp .env.example .env      # add OPENAI_API_KEY
docker compose up task4   # API at http://localhost:8004/docs
```

### Local
```bash
pip install -e .
cd task4_resume_ranker
export OPENAI_API_KEY=sk-...
uvicorn app.main:app --port 8004
```

## API

`POST /rank` (JSON)
```json
{ "job_description": "Senior Backend Engineer ...",
  "resumes": [ {"id": "c1", "text": "...resume text..."} ] }
```

`POST /rank/upload` (multipart) — `job_description` field + one or more resume files (PDF/txt).

Response:
```json
{ "job_description_summary": "...",
  "ranked": [
    { "id": "c1", "name": "Priya Nair", "score": 88.6,
      "semantic_score": 0.72, "rubric_score": 94,
      "strengths": ["Python/FastAPI", "AWS ECS", "Kafka", "PCI-DSS"],
      "gaps": ["..."], "justification": "..." } ],
  "skipped": [] }
```

### Try it with the sample data
The `data/` folder has one JD and four resumes (strong / partial / weak / cloud-heavy). A
helper to POST them:
```bash
python - <<'PY'
import requests, pathlib
d = pathlib.Path("data")
jd = (d/"job_description.txt").read_text()
resumes = [{"id": p.stem, "text": p.read_text()} for p in d.glob("resume_*.txt")]
r = requests.post("http://localhost:8004/rank", json={"job_description": jd, "resumes": resumes})
for c in r.json()["ranked"]:
    print(f"{c['score']:>6}  {c['id']:<14} gaps={c['gaps']}")
PY
```
Expected order: `resume_strong` ≥ `resume_midcloud` > `resume_partial` > `resume_weak`.

## How it meets the rubric
| Criterion | Weight | Where |
|-----------|--------|-------|
| Resume parsing | 20% | `parser.py` (PDF/txt) |
| LLM reasoning | 20% | `extractor.py` + rubric scoring in `scorer.py` |
| Ranking quality | 25% | hybrid `semantic + rubric`, deterministic sort |
| Architecture | 15% | isolated parse→extract→score→rank stages |
| Prompting | 10% | schema-locked prompts in `prompts.py` |
| Documentation | 10% | this file |
| Bonus | — | hybrid scoring, embeddings, structured JSON output |

## Tests
```bash
cd task4_resume_ranker && python -m pytest -q
```
