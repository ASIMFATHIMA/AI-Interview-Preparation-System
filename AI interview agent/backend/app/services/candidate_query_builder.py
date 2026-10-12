"""Build a grounded semantic query from stored parsed resume evidence."""


def build_candidate_query(candidate):
    skills = ", ".join(candidate.get("skills", [])) or "transferable technical skills"
    education = "; ".join(
        str(item.get("degree") or item.get("description") or "")
        for item in candidate.get("education", [])
        if isinstance(item, dict)
    ) or candidate.get("field_of_study") or "a related technical degree"
    projects = "; ".join(
        str(item.get("project_name") or item.get("description") or "")
        for item in candidate.get("projects", [])
        if isinstance(item, dict)
    ) or "academic and personal projects"
    experience = "; ".join(
        str(item.get("role") or item.get("description") or "")
        for item in candidate.get("experience", [])
        if isinstance(item, dict)
    ) or "early-career experience"
    return f"{education} student with {skills}. Projects: {projects}. Experience: {experience}. Looking for relevant internship or entry-level roles."
