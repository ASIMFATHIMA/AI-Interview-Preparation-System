"""Persistent local vector store using FAISS with metadata mapping and hybrid retrieval."""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.services.embedding_service import embed_texts

ROOT = Path(__file__).resolve().parents[3]
STORE_DIR = ROOT / "data" / "vector_store"
INDEX_PATH = STORE_DIR / "jobs.index"
VECTORS_PATH = STORE_DIR / "jobs_vectors.npy"
METADATA_PATH = STORE_DIR / "jobs_metadata.json"

DEFAULT_HYBRID_WEIGHTS = {
    "semantic": 0.65,
    "skill": 0.25,
    "domain": 0.10,
}


def build_index(chunks: List[Dict]):
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    texts = [chunk["text"] for chunk in chunks]
    vectors = embed_texts(texts)

    # Ensure L2-normalized float32 vectors for cosine similarity via inner product
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized_vectors = (vectors / norms).astype(np.float32)

    try:
        import faiss
        dimension = normalized_vectors.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(normalized_vectors)
        faiss.write_index(index, str(INDEX_PATH))
    except (ImportError, Exception):
        np.save(VECTORS_PATH, normalized_vectors)
        INDEX_PATH.write_text("numpy-fallback", encoding="utf-8")

    # Save metadata mapping each vector index to its chunk metadata
    # Metadata includes: job_id, chunk_id, job_title, company, section, text
    METADATA_PATH.write_text(json.dumps(chunks, indent=2), encoding="utf-8")
    return {
        "chunks": len(chunks),
        "dimension": int(normalized_vectors.shape[1]),
        "path": str(INDEX_PATH),
    }


def _load():
    if not METADATA_PATH.exists():
        return None, [], "none"
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    try:
        import faiss
        index = faiss.read_index(str(INDEX_PATH))
        return index, metadata, "faiss"
    except (ImportError, Exception):
        if VECTORS_PATH.exists():
            return np.load(VECTORS_PATH), metadata, "numpy"
        return None, metadata, "none"


def _normalize_tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9+#.-]+", str(text).casefold()) if len(t) > 1}


def search_jobs(
    query: str,
    top_k: int = 5,
    candidate_skills: Optional[List[str]] = None,
    candidate_domain: Optional[str] = None,
    hybrid: bool = False,
    weights: Optional[Dict[str, float]] = None,
):
    """Retrieve unique jobs using semantic similarity, deduplicating multi-chunk hits.
    
    Optionally combines semantic similarity with deterministic skill and domain relevance.
    """
    index, metadata, backend = _load()
    if backend == "none" or not metadata:
        return []

    # 1. Embed query and calculate cosine similarity
    query_vector = embed_texts([query])
    q_norm = np.linalg.norm(query_vector)
    if q_norm > 0:
        query_vector = (query_vector / q_norm).astype(np.float32)

    # Search top chunks (retrieve a generous pool so all jobs have chunks considered)
    pool_size = min(len(metadata), max(top_k * 10, 40))

    if backend == "faiss":
        scores, indices = index.search(query_vector, pool_size)
        ranked_chunks = list(zip(scores[0], indices[0]))
    else:
        scores = np.dot(index, query_vector[0])
        ranked_indices = np.argsort(scores)[::-1][:pool_size]
        ranked_chunks = [(scores[idx], idx) for idx in ranked_indices]

    # 2. Group chunks by job_id (Job-Level Deduplication)
    grouped: Dict[str, Dict] = {}
    for score, idx in ranked_chunks:
        if idx < 0 or idx >= len(metadata):
            continue
        chunk = metadata[idx]
        job_id = chunk["job_id"]
        chunk_score = float(score)

        if job_id not in grouped:
            grouped[job_id] = {
                "job_id": job_id,
                "job_title": chunk.get("job_title", ""),
                "company": chunk.get("company", ""),
                "similarity_score": chunk_score,
                "chunk_scores": [chunk_score],
                "matched_sections": [chunk["section"]],
                "chunk_texts": [chunk.get("text", "")],
            }
        else:
            entry = grouped[job_id]
            entry["chunk_scores"].append(chunk_score)
            if chunk_score > entry["similarity_score"]:
                entry["similarity_score"] = chunk_score
            if chunk["section"] not in entry["matched_sections"]:
                entry["matched_sections"].append(chunk["section"])
            entry["chunk_texts"].append(chunk.get("text", ""))

    # 3. Score calculation (pure semantic or hybrid)
    w = weights or DEFAULT_HYBRID_WEIGHTS
    query_tokens = _normalize_tokens(query)
    skill_tokens = set()
    if candidate_skills:
        for s in candidate_skills:
            skill_tokens.update(_normalize_tokens(s))

    results = []
    for job_id, entry in grouped.items():
        semantic_score = max(0.0, min(1.0, entry["similarity_score"]))

        if hybrid and (skill_tokens or candidate_domain):
            all_text = " ".join(entry["chunk_texts"]).casefold()
            job_title_tokens = _normalize_tokens(entry["job_title"])

            # Skill relevance
            if skill_tokens:
                matched_skill_cnt = sum(1 for token in skill_tokens if token in all_text)
                skill_score = min(1.0, matched_skill_cnt / max(1, len(skill_tokens)))
            else:
                skill_score = semantic_score

            # Domain / Title relevance
            domain_score = 0.0
            if candidate_domain:
                c_domain_tokens = _normalize_tokens(candidate_domain)
                if any(t in job_title_tokens or t in all_text for t in c_domain_tokens):
                    domain_score = 1.0
            elif any(t in job_title_tokens for t in query_tokens):
                domain_score = 0.8
            else:
                domain_score = semantic_score

            final_score = (
                w.get("semantic", 0.65) * semantic_score
                + w.get("skill", 0.25) * skill_score
                + w.get("domain", 0.10) * domain_score
            )
        else:
            final_score = semantic_score

        results.append({
            "job_id": job_id,
            "job_title": entry["job_title"],
            "company": entry["company"],
            "similarity_score": round(float(final_score), 4),
            "semantic_score": round(float(semantic_score), 4),
            "matched_sections": entry["matched_sections"],
        })

    # 4. Sort unique jobs descending by score and return top_k
    results.sort(key=lambda item: item["similarity_score"], reverse=True)
    return results[:top_k]
