# AI HR Recruitment Assistant

## Milestone 2

Milestone 2 adds a curated internship knowledge base and transparent job-resume matching without replacing the Milestone 1 profile and resume pipeline.

### M2.1 Dataset and Knowledge Base

- `data/jobs_dataset.json` and `data/jobs_dataset.csv` contain 180 curated sample internship and entry-level postings across AI, ML, data, Python, backend, full stack, software engineering, Generative AI, NLP, and cloud/DevOps.
- `backend/app/services/job_data_cleaner.py` normalizes text and skills, removes duplicates using company + title + location, detects incomplete/irrelevant records, and produces `data/cleaning_report.json`.
- The existing `jobs` table is extended with structured M2 fields. `backend/migrations/jobs_knowledge_base.sql` documents the SQL migration and application startup applies missing columns idempotently.
- `backend/scripts/import_jobs.py` imports records without inserting the same dataset ID twice.

### M2.2 RAG Pipeline and Semantic Search

The pipeline is:

```text
Job Dataset -> Clean and Normalize -> Job Documents -> Section Chunks
-> Embeddings -> Persisted Vector Store -> Semantic Retrieval
```

`job_document_builder.py` creates grounded documents, `job_chunker.py` preserves meaningful sections and metadata, and `embedding_service.py` uses `sentence-transformers/all-MiniLM-L6-v2` when installed. The current environment uses a deterministic NumPy fallback so development and tests do not require a model download. `vector_store.py` uses FAISS when installed and otherwise persists NumPy vectors and metadata.

Run:

```powershell
cd backend
..\venv\Scripts\python.exe scripts\generate_jobs_dataset.py
..\venv\Scripts\python.exe scripts\import_jobs.py
..\venv\Scripts\python.exe scripts\build_job_index.py
```

Semantic search is available at `POST /api/jobs/search` with `{ "query": "...", "top_k": 5 }`.

### M2.3 Job-Resume Matching Agent

The existing parsed resume tables are converted into a candidate query, used for top-k retrieval, and then scored programmatically against retrieved jobs. The default transparent weights are required skills 40%, preferred skills 15%, education 15%, experience 10%, projects 10%, and responsibilities/keywords 10%. The LLM is not used to invent or choose numeric scores; deterministic reasoning is returned from supplied evidence.

`POST /api/jobs/match-resume` accepts `{ "student_id": 1, "top_k": 10 }`. Authentication still determines the candidate and prevents matching another student's resume.

The existing `/jobs` and legacy `/api/matching/analyze` workflows remain available for Milestone 1 compatibility.

### Application Tracking

Authenticated students can add a job with `POST /applications` and view their records with `GET /applications`. On startup, the backend idempotently adds current tracker fields to an existing legacy `applications` table and backfills company names, deadlines, and job titles where possible.

### M2.4 Evaluation

Five sample profiles are stored in `data/evaluation_profiles.json`. Run:

```powershell
cd backend
..\venv\Scripts\python.exe evaluation\evaluate_all.py
```

The scripts calculate Precision@5, Recall@5, MRR, average match score, and top-rank relevance from the actual persisted index and write `data/evaluation_report.json`. The current measured report is:

```json
{
  "retrieval": {"precision_at_5": 0.4, "recall_at_5": 0.4, "mrr": 0.4},
  "matching": {"average_match_score": 69.0, "top_rank_relevance": 1.0}
}
```

The retrieval metrics identify a real improvement area: the lightweight fallback embedding and category relevance labeling need refinement for stronger top-five precision. Top-ranked match relevance is currently perfect for the five evaluation profiles.

### Frontend

The existing `/jobs` page is now the M2 dashboard. It supports semantic search, resume-based ranked matching, score/recommendation cards, matched and missing skills, and job details. The frontend still uses the existing Vite proxy and authenticated API client.

Architecture:

```text
Resume/Profile -> Candidate Query -> Embedding -> Vector Search
-> Relevant Jobs -> Programmatic Compatibility Score -> Grounded Reasoning
-> Ranked Internship Results
```
