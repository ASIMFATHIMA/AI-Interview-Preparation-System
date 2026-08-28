# Internship Application Co-Pilot

An AI-powered, multi-agent assistant that helps students go from resume → matched internships →
tailored applications → interview prep, grounded via RAG over real job postings.

This repo currently implements **Milestone 1: Foundation & Candidate Understanding**.

## What's in Milestone 1

- `docs/research.md` — M1.1: research on internship workflows, RAG, and multi-agent patterns.
- `docs/architecture.md` — M1.2: system architecture diagram, agent responsibilities,
  candidate profile schema (ERD), and resume → parsing → profile data flow.
- `docs/tech-stack.md` — full technology stack with rationale.
- `backend/` — FastAPI backend implementing:
  - M1.3: student profile creation + resume upload (`POST /students`,
    `POST /students/{id}/resume`).
  - M1.4: resume parsing (PDF/DOCX/TXT → raw text) and LLM-based structured extraction
    (skills, education, experience, projects) into a Candidate Profile
    (`POST /students/{id}/resume/{resume_id}/parse`, `GET /students/{id}/profile`).
  - `backend/sample_resumes/` — 3 varied sample resumes used to test extraction robustness.
  - `backend/tests/test_extraction.py` — extraction test/demo script.
- `frontend/` — minimal HTML/JS UI for profile creation + resume upload, calling the API above.

## Architecture at a glance

See `docs/architecture.md` for the full diagram and rationale. Summary:

```
Student UI → Backend API → Resume Storage → Resume Parsing (text extraction + LLM) → Candidate Profile (DB)
                                                                                            │
                                                                        (future milestones) ▼
                                                            AI Agent Layer (orchestrator + 5 specialist agents)
                                                                             │
                                                        RAG Pipeline ↔ Job-Posting Knowledge Base
```

Planned agents: **Resume Agent** (built in M1), **Job-Resume Matching Agent**, **Skill Gap
Agent**, **Cover Letter Agent**, **Interview Agent**, all coordinated by a **Career Assistant**
orchestrator (M2+).

## Getting Started

### Prerequisites
- Python 3.11+
- An Anthropic API key (for the LLM-based resume extraction step)

### Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY

uvicorn app.main:app --reload --port 8000
```

API docs (Swagger UI) will be available at `http://localhost:8000/docs`.

### Frontend

Just open `frontend/index.html` in a browser (it talks to `http://localhost:8000` by default —
edit `API_BASE` in `frontend/app.js` if you run the backend elsewhere).

### Test extraction on sample resumes

```bash
cd backend
python -m tests.test_extraction
```

This runs the full pipeline (text extraction + LLM structured extraction) against every file in
`sample_resumes/` and prints the resulting structured JSON for each.

You can also run it as a pytest suite (it auto-skips if `ANTHROPIC_API_KEY` isn't set):

```bash
pytest tests/test_extraction.py -v
```

## API Endpoints (Milestone 1)

| Method | Path | Purpose |
|---|---|---|
| POST | `/students` | Create a student profile |
| GET | `/students/{id}` | Get a student |
| GET | `/students` | List all students |
| POST | `/students/{id}/resume` | Upload a resume file (pdf/docx/txt) |
| GET | `/students/{id}/resumes` | List a student's uploaded resumes |
| POST | `/students/{id}/resume/{resume_id}/parse` | Parse + extract structured data from a resume |
| GET | `/students/{id}/profile` | Get the student's structured Candidate Profile |
| GET | `/health` | Health check |

## Roadmap (future milestones)

- **M2**: Job-Posting Knowledge Base + RAG pipeline (embeddings, vector store, retrieval),
  Job-Resume Matching Agent, Skill Gap Agent.
- **M3**: Cover Letter Agent, Application Tracking Module.
- **M4**: Interview Agent, Career Assistant orchestrator tying all agents together, polished
  frontend.

## Repository Structure

```
internship-copilot/
├── README.md
├── docs/
│   ├── research.md
│   ├── architecture.md
│   └── tech-stack.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── resume_parser.py
│   │   └── llm_extractor.py
│   ├── sample_resumes/
│   └── tests/
│       └── test_extraction.py
└── frontend/
    ├── index.html
    ├── app.js
    └── styles.css
```
