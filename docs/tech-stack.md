# Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend framework | **Python 3.11 + FastAPI** | Async-native, automatic OpenAPI/Swagger docs, easy to add agent routes incrementally, huge ecosystem for AI apps |
| Web server | **Uvicorn** | ASGI server for FastAPI |
| Database | **SQLite** (dev) → **PostgreSQL** (prod) | Zero-config for local dev; same SQLAlchemy models port directly to Postgres for production/team use |
| ORM | **SQLAlchemy 2.0** | Mature, DB-agnostic, migration-friendly (Alembic-ready) |
| Data validation | **Pydantic v2** | Request/response schemas, and used to validate/coerce LLM JSON output before persisting |
| File storage | Local disk (`/uploads`) for M1 | Swappable for S3/GCS later behind the same interface |
| PDF text extraction | **pdfplumber** | Reliable layout-aware text extraction from PDF resumes |
| DOCX text extraction | **python-docx** | Standard library for reading `.docx` |
| LLM | **Anthropic Claude (Messages API)** | Used for structured resume-field extraction now; will power Matching/Skill-Gap/Cover-Letter/Interview agents later |
| Agent orchestration (future) | Lightweight custom orchestrator (Python), upgradeable to LangGraph/CrewAI if complexity grows | Keeps M1 dependency-light; revisit in M2 if multi-agent state machines get complex |
| Vector store (future, M2) | **Chroma** (local) → pgvector/Pinecone (prod) | Needed once Job-Posting Knowledge Base + RAG pipeline are built |
| Frontend | Plain **HTML/CSS/JS** for M1 | Keeps M1 focused on backend/agent/data architecture; can migrate to React/Next.js later |
| Testing | **pytest** | Unit tests for parsing/extraction against sample resumes |
| Environment/config | `.env` + `python-dotenv` | Keep API keys out of source control |

## Why an LLM (not pure regex/rules) for resume parsing?

Resumes vary enormously in layout, section naming, and formatting (single-column, two-column,
tables, creative templates). Rule-based/regex parsers are brittle and break on non-standard
formats. An LLM given the raw extracted text and a strict JSON schema generalizes far better
across formats and can correctly attribute skills to the right context (e.g. distinguishing a
"Python" mentioned in a project from a "Python" mentioned as a language proficiency), while still
producing machine-readable, schema-validated output.
