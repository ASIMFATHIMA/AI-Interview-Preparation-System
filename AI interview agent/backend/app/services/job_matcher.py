"""Transparent, configurable candidate-to-job compatibility scoring."""
import re
from typing import Any, Dict, List, Optional

from app.services.job_data_cleaner import SKILL_ALIASES, clean_text

DEFAULT_WEIGHTS = {
    "required_skills": 0.40,
    "preferred_skills": 0.15,
    "education": 0.15,
    "experience": 0.10,
    "projects": 0.10,
    "responsibilities": 0.10,
}


def _norm(val: Any) -> str:
    cleaned = clean_text(str(val or "")).casefold()
    return SKILL_ALIASES.get(cleaned, cleaned)


def _norm_skill_set(skills: Any) -> set:
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    if not isinstance(skills, (list, set, tuple)):
        return set()
    result = set()
    for s in skills:
        ns = _norm(s)
        if ns:
            result.add(ns)
    return result


def _to_text(val: Any) -> str:
    if isinstance(val, list):
        items = []
        for v in val:
            if isinstance(v, dict):
                items.append(" ".join(str(x) for x in v.values()))
            else:
                items.append(str(v))
        return " ".join(items)
    if isinstance(val, dict):
        return " ".join(str(x) for x in val.values())
    return str(val or "")


def _match_skills(candidate_skill_set: set, target_skills: List[str]):
    matched = []
    missing = []
    for skill in target_skills:
        clean_skill = clean_text(skill)
        if not clean_skill:
            continue
        norm_target = _norm(clean_skill)
        # Check direct or alias match
        if norm_target in candidate_skill_set:
            matched.append(clean_skill)
            continue

        # Prevent false positives like "sql" in "postgresql" or "java" in "javascript"
        matched_flag = False
        target_tokens = set(re.findall(r"[a-z0-9+#]+", norm_target))
        for cs in candidate_skill_set:
            if cs == norm_target:
                matched_flag = True
                break
            cs_tokens = set(re.findall(r"[a-z0-9+#]+", cs))
            if len(target_tokens) > 1 and target_tokens == cs_tokens:
                matched_flag = True
                break
        if matched_flag:
            matched.append(clean_skill)
        else:
            missing.append(clean_skill)
    return matched, missing


def evaluate_education(candidate: Dict, job: Dict) -> float:
    """Compare candidate degree and field of study with job education requirements."""
    job_req = clean_text(job.get("education_requirements") or job.get("qualifications") or "").casefold()
    if not job_req:
        return 1.0

    cand_edu_text = _to_text(candidate.get("education", [])).casefold()
    cand_field = clean_text(candidate.get("field_of_study", "")).casefold()
    full_cand_text = f"{cand_edu_text} {cand_field}"

    # Relevant degree keywords
    degrees = ["b.tech", "b.e", "btech", "be", "b.sc", "bsc", "bca", "m.tech", "mtech", "m.sc", "msc", "mca", "bachelor", "master"]
    has_degree_match = any(d in full_cand_text for d in degrees) or not any(d in job_req for d in degrees)

    # Relevant domain/field keywords
    fields = [
        "computer science", "information technology", "artificial intelligence",
        "data science", "software", "engineering", "statistics", "mathematics",
        "cybersecurity", "cyber", "analytics", "it", "cs", "ai"
    ]
    has_field_match = any(f in full_cand_text for f in fields) or not any(f in job_req for f in fields)

    if has_degree_match and has_field_match:
        return 1.0
    if has_degree_match or has_field_match:
        return 0.7
    return 0.3


def evaluate_experience(candidate: Dict, job: Dict) -> float:
    """Compare candidate experience with job requirements. Supports freshers/interns."""
    job_exp = clean_text(job.get("experience_requirements") or job.get("experience") or "").casefold()
    cand_exp = candidate.get("experience", [])
    cand_projects = candidate.get("projects", [])

    is_entry_or_intern = any(kw in job_exp for kw in ["0-1", "fresher", "intern", "academic", "student", "entry"]) or not job_exp

    if is_entry_or_intern:
        # If candidate has any internship experience, perfect match
        if cand_exp:
            return 1.0
        # If student has relevant academic/personal projects, high match for early career
        if cand_projects:
            return 0.9
        return 0.75

    # If job specifically requires more experience (> 1-2 years)
    if cand_exp:
        return 0.8
    return 0.4


def evaluate_projects(candidate: Dict, job: Dict) -> float:
    """Compare candidate projects against job domain, responsibilities, and technologies."""
    cand_projects = candidate.get("projects", [])
    if not cand_projects:
        return 0.0

    project_text = _to_text(cand_projects).casefold()
    domain = clean_text(job.get("projects_or_domain") or "").casefold()
    keywords = [_norm(k) for k in (job.get("keywords") or [])]
    required = [_norm(k) for k in (job.get("required_skills") or [])]

    matched_indicators = 0
    total_indicators = len(keywords) + (1 if domain else 0)
    if total_indicators == 0:
        return 1.0

    if domain and any(w in project_text for w in domain.split() if len(w) > 3):
        matched_indicators += 2

    for kw in keywords + required:
        if kw and kw in project_text:
            matched_indicators += 1

    return min(1.0, max(0.2, matched_indicators / max(1, len(keywords) or 3)))


def evaluate_responsibilities(candidate_skill_set: set, candidate: Dict, job: Dict) -> float:
    """Compare job responsibilities with candidate demonstrated skills, projects, and experience."""
    resp_list = job.get("responsibilities", [])
    if not resp_list:
        return 1.0

    resp_text = _to_text(resp_list).casefold()
    cand_context = f"{' '.join(candidate_skill_set)} {_to_text(candidate.get('projects', []))} {_to_text(candidate.get('experience', []))}".casefold()

    # Check how many skills or project terms are reflected in responsibilities
    matches = 0
    for skill in candidate_skill_set:
        if len(skill) > 2 and skill in resp_text:
            matches += 1

    # Ratio of matched technical responsibilities
    return min(1.0, max(0.2, matches / max(1, min(len(candidate_skill_set), 4))))


def calculate_match(candidate: Dict, job: Dict, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    w = weights or DEFAULT_WEIGHTS

    cand_skills = candidate.get("skills", [])
    candidate_skill_set = _norm_skill_set(cand_skills)

    required_skills = list(job.get("required_skills") or [])
    preferred_skills = list(job.get("preferred_skills") or [])

    matched_required, missing_required = _match_skills(candidate_skill_set, required_skills)
    matched_preferred, missing_preferred = _match_skills(candidate_skill_set, preferred_skills)

    req_score = len(matched_required) / len(required_skills) if required_skills else 1.0
    pref_score = len(matched_preferred) / len(preferred_skills) if preferred_skills else 1.0
    edu_score = evaluate_education(candidate, job)
    exp_score = evaluate_experience(candidate, job)
    proj_score = evaluate_projects(candidate, job)
    resp_score = evaluate_responsibilities(candidate_skill_set, candidate, job)

    component_scores = {
        "required_skills": round(float(req_score), 3),
        "preferred_skills": round(float(pref_score), 3),
        "education": round(float(edu_score), 3),
        "experience": round(float(exp_score), 3),
        "projects": round(float(proj_score), 3),
        "responsibilities": round(float(resp_score), 3),
    }

    total_weight = sum(w.get(k, 0) for k in component_scores)
    weighted_sum = sum(component_scores[k] * w.get(k, 0) for k in component_scores)
    final_score = round(100 * (weighted_sum / total_weight), 1) if total_weight > 0 else 0.0

    if final_score >= 80:
        recommendation = "Strong Match"
    elif final_score >= 65:
        recommendation = "Good Match"
    elif final_score >= 45:
        recommendation = "Partial Match"
    else:
        recommendation = "Low Match"

    return {
        "match_score": final_score,
        "matched_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "education_match": edu_score >= 0.7,
        "experience_match": exp_score >= 0.7,
        "project_match": proj_score >= 0.5,
        "component_scores": component_scores,
        "recommendation": recommendation,
    }


def explain_match(candidate: Dict, job: Dict, result: Dict) -> str:
    matched = ", ".join(result["matched_skills"]) or "foundational problem-solving capabilities"
    missing = ", ".join(result["missing_required_skills"]) or "none"
    edu_str = "aligns well with role requirements" if result["education_match"] else "partially satisfies domain prerequisites"
    exp_str = "satisfies entry-level expectations" if result["experience_match"] else "shows early-stage readiness"

    return (
        f"The candidate demonstrates matching capabilities in {matched}. "
        f"Their academic background {edu_str}, and their project experience {exp_str}. "
        f"Missing required skills identified: {missing}. "
        f"The overall programmatic compatibility score is {result['match_score']:.1f}%, calculated from configured "
        f"weights for required skills (40%), preferred skills (15%), education (15%), experience (10%), projects (10%), and responsibilities (10%)."
    )
