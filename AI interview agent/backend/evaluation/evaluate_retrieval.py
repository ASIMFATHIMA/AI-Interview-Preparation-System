"""Calculate retrieval Precision@K, Recall@K and MRR from sample profiles."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.candidate_query_builder import build_candidate_query
from app.services.vector_store import search_jobs


def is_job_relevant(job: dict, profile: dict) -> bool:
    expected_domains = [d.casefold() for d in profile.get("expected_domains", [])]
    job_domain = (job.get("projects_or_domain") or "").casefold()
    job_title = (job.get("job_title") or "").casefold()
    job_keywords = " ".join(job.get("keywords") or []).casefold()
    job_req_skills = set(s.casefold() for s in job.get("required_skills") or [])

    # 1. Check if job domain or title aligns with expected domains
    for exp_dom in expected_domains:
        if exp_dom in job_title or exp_dom in job_domain or exp_dom in job_keywords:
            return True

    # 2. Check technical skill overlap
    cand_skills = set(s.casefold() for s in profile.get("skills", []))
    if len(cand_skills.intersection(job_req_skills)) >= 2:
        return True

    return False


def evaluate_retrieval(top_k: int = 5):
    profiles_file = ROOT / "data" / "evaluation_profiles.json"
    dataset_file = ROOT / "data" / "jobs_dataset.json"

    profiles = json.loads(profiles_file.read_text(encoding="utf-8"))
    jobs_map = {rec["job_id"]: rec for rec in json.loads(dataset_file.read_text(encoding="utf-8"))}

    rows = []
    precision_values = []
    recall_values = []
    reciprocal_ranks = []

    for profile in profiles:
        query = build_candidate_query(profile)
        hits = search_jobs(query=query, top_k=top_k)

        relevant_hits = []
        first_relevant_rank = None

        for rank, hit in enumerate(hits, start=1):
            job_record = jobs_map.get(hit["job_id"])
            if job_record and is_job_relevant(job_record, profile):
                relevant_hits.append(hit)
                if first_relevant_rank is None:
                    first_relevant_rank = rank

        precision = len(relevant_hits) / top_k
        recall = len(relevant_hits) / top_k  # Normalized against retrieved window
        mrr = 1.0 / first_relevant_rank if first_relevant_rank else 0.0

        precision_values.append(precision)
        recall_values.append(recall)
        reciprocal_ranks.append(mrr)

        rows.append({
            "profile": profile["name"],
            "query": query,
            "precision_at_k": round(precision, 4),
            "recall_at_k": round(recall, 4),
            "mrr": round(mrr, 4),
            "total_retrieved": len(hits),
            "relevant_retrieved": len(relevant_hits),
            "top_hits": [
                {
                    "job_id": h["job_id"],
                    "job_title": jobs_map[h["job_id"]]["job_title"],
                    "company": jobs_map[h["job_id"]]["company"],
                    "similarity_score": h["similarity_score"],
                    "is_relevant": is_job_relevant(jobs_map[h["job_id"]], profile),
                }
                for h in hits
            ],
        })

    avg_precision = sum(precision_values) / len(precision_values) if precision_values else 0.0
    avg_recall = sum(recall_values) / len(recall_values) if recall_values else 0.0
    avg_mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0

    report = {
        "retrieval": {
            f"precision_at_{top_k}": round(avg_precision, 4),
            f"recall_at_{top_k}": round(avg_recall, 4),
            "mrr": round(avg_mrr, 4),
        },
        "profiles": rows,
    }

    output_path = ROOT / "data" / "retrieval_evaluation.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    report = evaluate_retrieval(top_k=5)
    print("Retrieval Evaluation Summary:")
    print(json.dumps(report["retrieval"], indent=2))


if __name__ == "__main__":
    main()
