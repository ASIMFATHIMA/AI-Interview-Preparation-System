"""Calculate deterministic match scores and top-rank relevance for the sample profiles."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.candidate_query_builder import build_candidate_query
from app.services.job_matcher import calculate_match
from app.services.vector_store import search_jobs
from evaluation.evaluate_retrieval import is_job_relevant


def evaluate_matching(top_k: int = 5):
    profiles_file = ROOT / "data" / "evaluation_profiles.json"
    dataset_file = ROOT / "data" / "jobs_dataset.json"

    profiles = json.loads(profiles_file.read_text(encoding="utf-8"))
    jobs = {record["job_id"]: record for record in json.loads(dataset_file.read_text(encoding="utf-8"))}

    rows = []
    all_scores = []
    top_rank_relevant = []

    for profile in profiles:
        query = build_candidate_query(profile)
        hits = search_jobs(
            query=query,
            top_k=top_k,
            candidate_skills=profile.get("skills", []),
            candidate_domain=profile.get("field_of_study"),
            hybrid=True,
        )

        ranked = []
        for hit in hits:
            job = jobs[hit["job_id"]]
            result = calculate_match(profile, job)
            relevant = is_job_relevant(job, profile)
            ranked.append({
                "job_id": hit["job_id"],
                "job_title": job["job_title"],
                "company": job["company"],
                "match_score": result["match_score"],
                "recommendation": result["recommendation"],
                "matched_skills": result["matched_skills"],
                "missing_required_skills": result["missing_required_skills"],
                "component_scores": result["component_scores"],
                "is_domain_relevant": relevant,
            })
            all_scores.append(result["match_score"])

        ranked.sort(key=lambda item: item["match_score"], reverse=True)

        # Check if #1 ranked role is relevant and has strong/good match
        is_top_relevant = 1.0 if ranked and ranked[0]["is_domain_relevant"] and ranked[0]["match_score"] >= 60.0 else 0.0
        top_rank_relevant.append(is_top_relevant)

        rows.append({
            "profile": profile["name"],
            "top_match": ranked[0] if ranked else None,
            "average_profile_score": round(sum(r["match_score"] for r in ranked) / len(ranked), 2) if ranked else 0.0,
            "matches": ranked,
        })

    avg_match_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
    top_rank_relevance_rate = round(sum(top_rank_relevant) / len(top_rank_relevant), 2) if top_rank_relevant else 0.0

    report = {
        "matching": {
            "average_match_score": avg_match_score,
            "top_rank_relevance": top_rank_relevance_rate,
            "total_evaluations": len(all_scores),
        },
        "profiles": rows,
    }

    output_path = ROOT / "data" / "matching_evaluation.json"
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    report = evaluate_matching(top_k=5)
    print("Matching Evaluation Summary:")
    print(json.dumps(report["matching"], indent=2))


if __name__ == "__main__":
    main()
