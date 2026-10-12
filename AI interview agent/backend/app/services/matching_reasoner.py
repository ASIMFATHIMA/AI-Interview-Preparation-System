"""Optional grounded explanation layer for deterministic match results."""
import json

from app.services.job_matcher import explain_match
from app.services.llm_resume_extractor import client


def generate_matching_reasoning(candidate, job, result):
    fallback = explain_match(candidate, job, result)
    if not client:
        return fallback
    prompt = f"""
Explain this candidate/job match using only the supplied JSON evidence.
Do not add skills, education, experience, or requirements that are not present.
Do not change or recalculate the numeric score. Return a concise paragraph.
Candidate: {json.dumps(candidate, ensure_ascii=True)}
Job: {json.dumps(job, ensure_ascii=True)}
Programmatic result: {json.dumps(result, ensure_ascii=True)}
"""
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = (response.text or "").strip()
        return text or fallback
    except Exception:
        return fallback
