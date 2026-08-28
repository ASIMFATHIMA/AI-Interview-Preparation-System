# M1.1 — Research & Technical Understanding

## 1. Internship Application Workflows

A typical student internship application journey looks like this:

1. **Profile creation** — student registers and fills basic info (name, contact, education).
2. **Resume upload** — student uploads a resume (PDF/DOCX). Many platforms (LinkedIn, Handshake,
   Internshala) auto-parse this into a structured profile so it can be reused across applications.
3. **Job discovery** — student browses/searches internship postings, often filtered by role,
   location, skill match, or stipend.
4. **Matching & gap analysis** — platforms increasingly show a "match score" between the
   candidate's skills and a job's requirements, plus what's missing (skill gap).
5. **Application materials** — resume tailoring and a cover letter, often per-job.
6. **Submission & tracking** — student submits and then tracks status (applied / shortlisted /
   interview / offer / rejected).
7. **Interview preparation** — practicing likely questions based on the role and the student's
   background.
8. **Continuous improvement** — career guidance / suggestions for upskilling based on gaps found
   across multiple applications.

**Implication for our system:** each step above maps naturally to a distinct, focused agent
(see M1.2) rather than one monolithic "do everything" agent. This keeps prompts smaller, outputs
more testable, and lets us swap/improve one stage without breaking others.

## 2. RAG (Retrieval-Augmented Generation) Architecture

RAG solves a core LLM limitation: models don't inherently "know" your private, fast-changing
data (in our case: job postings, company requirements, the student's own resume history).

Standard RAG pipeline:

1. **Ingestion** — source documents (job postings, resumes, company FAQs) are cleaned and split
   into chunks.
2. **Embedding** — each chunk is converted into a vector using an embedding model.
3. **Vector storage** — vectors + metadata are stored in a vector database/index
   (e.g. Chroma, FAISS, pgvector, Pinecone).
4. **Retrieval** — at query time, the user's query (or an agent's need, e.g. "find postings
   matching this skillset") is embedded and the most similar chunks are retrieved via
   cosine/inner-product similarity, optionally re-ranked.
5. **Augmentation** — retrieved chunks are inserted into the LLM prompt as context.
6. **Generation** — the LLM generates a grounded answer/output (a match explanation, a tailored
   cover letter, an interview question) using both the retrieved context and its own reasoning.

**Where RAG fits in our system:**
- The **Job-Posting Knowledge Base** is the retrieval corpus (job descriptions, required skills).
- The **Candidate Profile** (structured resume data) acts as the query side for matching.
- Later milestones (Job-Resume Matching Agent, Skill Gap Agent, Cover Letter Agent) will all
  call the RAG pipeline to ground their outputs in real job postings instead of hallucinating
  requirements.
- For M1 specifically, we don't yet need retrieval — we need clean, structured extraction
  (parsing) that will *become* one side of the future RAG matching pipeline.

## 3. Multi-Agent Design Patterns

Patterns considered:

| Pattern | Description | Fit for this project |
|---|---|---|
| **Single monolithic agent** | One LLM call/prompt handles everything | Poor — prompts become huge, hard to debug, hard to extend per-milestone |
| **Pipeline (sequential) agents** | Fixed order: Resume Agent → Matching Agent → Skill Gap Agent → Cover Letter Agent | Good — matches the natural workflow, easy to reason about, easy to test each stage in isolation |
| **Orchestrator + specialist agents** | A "Career Assistant" orchestrator routes requests to specialist agents (Resume, Matching, Skill Gap, Cover Letter, Interview) based on user intent | **Chosen** — combines the clarity of the pipeline with flexibility (student can ask for just a cover letter, or just interview prep, without re-running the whole pipeline) |
| **Debate/critique agents** | Multiple agents critique each other's output | Overkill for M1; could be explored later for cover-letter quality review |

**Decision:** We adopt an **orchestrator + specialist agents** pattern:
- A lightweight **Career Assistant (orchestrator)** receives the student's request/intent.
- It delegates to the right **specialist agent**: Resume Agent, Job-Resume Matching Agent,
  Skill Gap Agent, Cover Letter Agent, or Interview Agent.
- Each specialist agent is a thin wrapper around (a) a focused prompt/tool, and (b) shared
  services: the Candidate Profile store and the RAG pipeline over the Job-Posting Knowledge Base.
- Agents communicate through a shared, structured **Candidate Profile** object (not free-text),
  so outputs are composable and auditable.

## 4. Technology Choices (summary — see `tech-stack.md` for full detail)

- **Backend:** Python + FastAPI (async, auto-generated OpenAPI docs, easy to add agent endpoints
  incrementally milestone by milestone).
- **Database:** SQLite for local dev / PostgreSQL for production, via SQLAlchemy ORM (easy
  migration path, no lock-in).
- **LLM:** Anthropic Claude (Messages API) for both structured extraction (resume parsing) and,
  in later milestones, generation (cover letters, interview Q&A) and agent orchestration.
- **Resume parsing:** `pdfplumber` (PDF text), `python-docx` (DOCX text) for raw text extraction,
  then an LLM call constrained to a strict JSON schema for structured extraction (chosen over
  pure regex/rule-based parsing because resumes are extremely unstructured/inconsistent in
  layout, and an LLM generalizes far better across formats).
- **Vector store (future milestone):** Chroma (local, zero-infra) to start; swappable for
  pgvector/Pinecone later — this is what will back the RAG pipeline over job postings.
- **Frontend:** Simple HTML/JS for M1 (profile creation + resume upload UI) to keep the
  milestone focused on backend/agent architecture; can be upgraded to React later.
