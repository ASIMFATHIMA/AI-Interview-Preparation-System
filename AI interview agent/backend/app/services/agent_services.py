"""Deterministic agent services built on verified candidate evidence."""
import json
import re
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.agents import (
    CareerChat,
    CoverLetter,
    Interview,
    InterviewQuestion,
    Job,
    JobMatch,
    SkillGapReport,
    TailoredResume,
)
from app.models.student import Student
from app.schemas.agents import (
    CoverLetterRequest,
    InterviewAnswerRequest,
    InterviewPrepRequest,
    InterviewStartRequest,
    JobCreate,
    MatchingRequest,
    ResumeCustomizeRequest,
    SkillGapRequest,
)
from app.services.ollama_client import generate_text, is_available
from app.services.resume_parser import get_parsed_data


def _json(value: Any) -> str:
    return json.dumps(value or [])


def _load(value: Optional[str], default: Any = None) -> Any:
    if not value:
        return [] if default is None else default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return [] if default is None else default


def _words(values: List[str]) -> set[str]:
    return {str(value).strip().lower() for value in values if str(value).strip()}


SKILL_ALIASES = {
    "fast api": "FastAPI", "fastapi": "FastAPI", "amazon web services": "AWS", "aws": "AWS",
    "restful api": "REST API", "restful apis": "REST API", "rest api": "REST API", "rest apis": "REST API",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL", "my sql": "MySQL", "mysql": "MySQL",
    "k8s": "Kubernetes", "ci/cd": "CI/CD", "continuous integration": "CI/CD",
}
KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C", "React", "Node.js", "Django", "Flask", "FastAPI",
    "REST API", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git",
    "GitHub Actions", "CI/CD", "Machine Learning", "Deep Learning", "Artificial Intelligence", "Generative AI", "LLM",
    "RAG", "NLP", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn", "Linux",
]
RELATED_SKILLS = {
    "FastAPI": {"Flask", "Django"}, "AWS": {"Azure", "GCP"}, "PostgreSQL": {"MySQL", "SQL"},
    "Docker": {"Kubernetes"}, "React": {"JavaScript", "TypeScript"}, "Machine Learning": {"Python", "Scikit-learn"},
}


def normalize_skill(value: str) -> str:
    clean = re.sub(r"\s+", " ", str(value).strip())
    lowered = clean.lower()
    return SKILL_ALIASES.get(lowered, next((skill for skill in KNOWN_SKILLS if skill.lower() == lowered), clean))


def extract_job_skills(job: Job) -> tuple[list[str], list[str]]:
    text = " ".join(filter(None, [job.title, job.description, job.responsibilities, job.technologies, job.experience]))
    detected = []
    lowered = text.lower()
    for skill in KNOWN_SKILLS:
        if re.search(r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)", lowered):
            detected.append(skill)
    explicit_required = [_normalize for _normalize in (_normal_skill(skill) for skill in _load(job.required_skills)) if _normalize]
    explicit_preferred = [_normalize for _normalize in (_normal_skill(skill) for skill in _load(job.preferred_skills)) if _normalize]
    required = list(dict.fromkeys(explicit_required + [skill for skill in detected if skill not in explicit_preferred]))
    preferred = list(dict.fromkeys(explicit_preferred))
    return required, preferred


def _normal_skill(skill: str) -> str:
    return normalize_skill(skill) if str(skill).strip() else ""


def _skill_recommendation(skill: str, current: list[str]) -> tuple[str, list[str], str]:
    related = ", ".join(sorted(RELATED_SKILLS.get(skill, set())))
    context = f"Since you already know {', '.join(current[:4])}, " if current else ""
    paths = {
        "FastAPI": ["Routing and REST APIs", "Pydantic models", "Dependency injection", "Authentication and database integration"],
        "Docker": ["Images and containers", "Dockerfiles", "Docker Compose", "Containerize a Python application"],
        "AWS": ["IAM fundamentals", "EC2 deployment", "S3 and RDS", "Deploy a production API"],
    }
    learning = paths.get(skill, [f"{skill} fundamentals", f"Practice {skill} with a small project", f"Apply {skill} in a job-relevant project"])
    recommendation = f"{context}focus on {', '.join(learning[:3])}."
    project = f"Build a small project using {skill}" + (f" with your {related} experience." if related else ".")
    return recommendation, learning, project


def create_job(db: Session, data: JobCreate) -> Job:
    job = Job(**data.model_dump(exclude={"required_skills", "preferred_skills", "technologies", "responsibilities"}))
    job.required_skills = _json(data.required_skills)
    job.preferred_skills = _json(data.preferred_skills)
    job.technologies = _json(data.technologies)
    job.responsibilities = _json(data.responsibilities)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> Job:
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def job_to_dict(job: Job) -> dict:
    return {
        "job_id": job.job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "experience": job.experience,
        "required_skills": _load(job.required_skills),
        "preferred_skills": _load(job.preferred_skills),
        "education_requirements": job.education_requirements,
        "responsibilities": _load(job.responsibilities),
        "technologies": _load(job.technologies),
        "description": job.description,
        "created_at": job.created_at,
    }


def candidate_context(db: Session, student: Student) -> dict:
    parsed = get_parsed_data(db=db, student_id=student.student_id)
    return {
        "student_id": student.student_id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone or "",
        "degree": student.degree or "",
        "field_of_study": student.field_of_study or "",
        "institution": student.institution or "",
        "location": student.location or "",
        "linkedin_url": student.linkedin_url or "",
        "github_url": student.github_url or "",
        "portfolio_url": student.portfolio_url or "",
        "skills": parsed.get("skills", []),
        "education": parsed.get("education", []),
        "experience": parsed.get("experience", []),
        "projects": parsed.get("projects", []),
        "certifications": parsed.get("certifications", []),
        "achievements": parsed.get("achievements", []),
        "raw_resume_text": student.raw_resume_text or "",
    }


def _experience_score(context: dict, job: Job) -> int:
    if not job.experience:
        return 100
    text = " ".join(str(item) for item in context["experience"]).lower()
    numbers = [int(value) for value in re.findall(r"\b(\d+)\s*\+?\s*years?", job.experience.lower())]
    required = numbers[0] if numbers else 1
    return 100 if text else 0 if required else 50


def _education_score(context: dict, job: Job) -> int:
    if not job.education_requirements:
        return 100
    haystack = " ".join(
        [str(context.get("degree") or ""), str(context.get("field_of_study") or ""), str(context.get("education"))]
    ).lower()
    required_words = _words(re.findall(r"[a-zA-Z]+", job.education_requirements))
    return 100 if required_words and any(word in haystack for word in required_words) else 0


def analyze_match(db: Session, student: Student, request: MatchingRequest) -> dict:
    job = get_job(db, request.job_id) if request.job_id else None
    if request.job:
        job_data = request.job
        required = job_data.required_skills
        preferred = job_data.preferred_skills
        job_text = job_data.description
        experience = job_data.experience
        education = job_data.education_requirements
        projects_text = job_data.title
    elif job:
        required = _load(job.required_skills)
        preferred = _load(job.preferred_skills)
        job_text = job.description
        experience = job.experience
        education = job.education_requirements
        projects_text = job.title
    else:
        raise HTTPException(status_code=400, detail="Provide job_id or an inline job description")

    context = candidate_context(db, student)
    candidate_skills = _words(context["skills"])
    required_words = _words(required)
    matched = sorted({skill for skill in required if skill.lower() in candidate_skills})
    missing = sorted({skill for skill in required if skill.lower() not in candidate_skills})
    skill_score = round((len(matched) / len(required)) * 100) if required else 100
    experience_score = _experience_score(context, job) if job else (100 if context["experience"] else 0)
    education_score = _education_score(context, job) if job else 100
    project_text = " ".join(str(item) for item in context["projects"]).lower()
    project_score = 100 if not projects_text or any(word in project_text for word in _words(projects_text.split())) else (60 if context["projects"] else 0)
    weights = [request.skill_weight, request.experience_weight, request.education_weight, request.project_weight]
    total = sum(weights)
    if total <= 0:
        raise HTTPException(status_code=400, detail="At least one scoring weight must be greater than zero")
    score = round((skill_score * weights[0] + experience_score * weights[1] + education_score * weights[2] + project_score * weights[3]) / total)
    recommendation = "Strong match" if score >= 80 else "Good match" if score >= 60 else "Partial match" if score >= 40 else "Low match"
    result = {
        "job_id": job.job_id if job else None,
        "match_score": score,
        "skill_score": skill_score,
        "experience_score": experience_score,
        "education_score": education_score,
        "project_score": project_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "recommendation": recommendation,
        "explanation": f"Matched {len(matched)} of {len(required)} required skills. Weights: skills {request.skill_weight:.0%}, experience {request.experience_weight:.0%}, education {request.education_weight:.0%}, projects {request.project_weight:.0%}.",
    }
    if job:
        record = JobMatch(
            student_id=student.student_id,
            job_id=job.job_id,
            matched_skills=_json(matched),
            missing_skills=_json(missing),
            recommendation=recommendation,
            explanation=result["explanation"],
            **{key: result[key] for key in ("match_score", "skill_score", "experience_score", "education_score", "project_score")},
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        result["match_id"] = record.match_id
    return result


def analyze_skill_gap(db: Session, student: Student, request: SkillGapRequest) -> dict:
    job = get_job(db, request.job_id) if request.job_id else None
    if not job and (request.job_description or request.job_title):
        job = SimpleNamespace(
            job_id=None,
            title=request.job_title or request.target_role or "Target role",
            company=request.company or "Target company",
            description=request.job_description or "",
            responsibilities=None,
            technologies="",
            experience=None,
            education_requirements=None,
            required_skills=_json(request.required_skills),
            preferred_skills=_json(request.preferred_skills),
        )
    if job:
        required, preferred = extract_job_skills(job)
    else:
        required = [_normal_skill(skill) for skill in request.required_skills]
        preferred = [_normal_skill(skill) for skill in request.preferred_skills]
    if not required and not preferred:
        raise HTTPException(status_code=400, detail="Unable to identify job skills. Provide a job with required skills or a valid job description.")
    context = candidate_context(db, student)
    current = list(dict.fromkeys(normalize_skill(skill) for skill in context["skills"]))
    current_words = {skill.lower() for skill in current}

    matched, partial, missing, preferred_missing, gaps = [], [], [], [], []
    for skill in list(dict.fromkeys(required + preferred)):
        is_required = skill in required
        if skill.lower() in current_words:
            matched.append(skill)
            continue
        related = RELATED_SKILLS.get(skill, set()) & set(current)
        if related:
            partial.append(skill)
            status = "partial"
            current_level = "Beginner"
        else:
            if is_required:
                missing.append(skill)
            else:
                preferred_missing.append(skill)
            status = "missing"
            current_level = "None"
        recommendation, learning_path, project = _skill_recommendation(skill, current)
        priority = "High" if is_required and not related else "Medium" if is_required or related else "Low"
        req_type = "Required" if is_required else "Preferred"
        gaps.append({
            "skill": skill,
            "requirement_type": req_type,
            "status": status,
            "priority": priority,
            "current_level": current_level,
            "required_level": "Intermediate",
            "why_it_matters": f"The selected role specifies {skill} as a {req_type.lower()} requirement.",
            "reason": f"{skill} is {req_type.lower()} by the target job.",
            "recommended_action": f"Learn {skill} core concepts and build a hands-on project.",
            "recommendation": recommendation,
            "suggested_topic_project": project,
            "project_recommendation": project,
            "learning_path": learning_path,
            "estimated_difficulty": "Medium",
            "gap_description": f"{skill} is {'partially covered by related skills' if related else 'not present'} in the candidate evidence.",
        })

    # Experience gaps
    experience_gaps = []
    if job and getattr(job, "experience", None):
        exp_score = _experience_score(context, job)
        if exp_score < 70:
            experience_gaps.append(f"Target role specifies '{job.experience}', while profile demonstrates student/entry-level experience.")
    elif not context["experience"]:
        experience_gaps.append("No industry work experience demonstrated (student/entry-level candidate).")

    # Qualification gaps
    qualification_gaps = []
    if job and getattr(job, "education_requirements", None):
        edu_score = _education_score(context, job)
        if edu_score < 50:
            qualification_gaps.append(f"Target role requests '{job.education_requirements}'. Verified student degree: '{context.get('degree') or 'Not specified'}'.")

    # Project gaps
    project_gaps = []
    if missing:
        project_gaps.append(f"No practical projects demonstrated utilizing {', '.join(missing[:3])}.")
    elif not context["projects"]:
        project_gaps.append("Add 1-2 portfolio projects to strengthen application.")

    # Actionable recommendations
    recommendations = []
    for s in missing[:3]:
        recommendations.append(f"Learn {s} core fundamentals and practical workflows.")
    if partial:
        recommendations.append(f"Deepen hands-on proficiency in {partial[0]} with production use-cases.")
    if missing:
        recommendations.append(f"Build a portfolio project incorporating {missing[0]}.")
    if not recommendations:
        recommendations.append("Review interview preparation questions to practice articulating your demonstrated skills.")

    total_required = len(required)
    required_matched = len([skill for skill in required if skill in matched])
    required_partial = len([skill for skill in required if skill in partial])
    skill_match_score = round(((required_matched + required_partial * 0.5) / total_required) * 100) if total_required else 100
    roadmap = [{"step": index, "skill": gap["skill"], "priority": gap["priority"], "status": gap["status"], "duration": "1-2 weeks", "learning_path": gap["learning_path"]} for index, gap in enumerate(sorted(gaps, key=lambda item: {"High": 0, "Medium": 1, "Low": 2}[item["priority"]]), 1)]

    report_data = {
        "matching_skills": matched,
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
        "preferred_missing_skills": preferred_missing,
        "experience_gaps": experience_gaps,
        "qualification_gaps": qualification_gaps,
        "project_gaps": project_gaps,
        "recommendations": recommendations,
        "skill_match_score": skill_match_score,
        "skill_gap_score": 100 - skill_match_score,
        "learning_roadmap": roadmap,
        "skill_gaps": gaps,
        "current_skills": current,
        "required_skills": list(dict.fromkeys(required + preferred)),
    }
    report = SkillGapReport(
        student_id=student.student_id,
        job_id=job.job_id if job and getattr(job, "job_id", None) else None,
        target_role=request.job_title or request.target_role or (job.title if job else None),
        gaps=_json(report_data),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {
        "success": True,
        "report_id": report.report_id,
        "candidate_id": student.student_id,
        "job_id": job.job_id if job and getattr(job, "job_id", None) else None,
        "job_title": job.title if job else report.target_role,
        "company": getattr(job, "company", request.company),
        "target_role": report.target_role,
        **report_data,
    }


def customize_resume(db: Session, student: Student, request: ResumeCustomizeRequest) -> dict:
    job = get_job(db, request.job_id) if request.job_id else None
    target_title = request.job_title or (job.title if job else "Software Engineer Intern")
    target_company = request.company or (job.company if job else "Target Company")
    job_desc = request.job_description or (job.description if job else "")

    if job:
        required, preferred = extract_job_skills(job)
        job_keywords = list(dict.fromkeys(required + preferred + _load(job.technologies)))
    else:
        job_keywords = [skill for skill in KNOWN_SKILLS if re.search(r"\b" + re.escape(skill.lower()) + r"\b", (job_desc + " " + target_title).lower())]

    context = candidate_context(db, student)
    student_skills = context.get("skills", [])

    norm_candidate = {normalize_skill(s).lower(): s for s in student_skills}
    relevant_skills = []
    keywords_used = []
    for kw in job_keywords:
        nkw = normalize_skill(kw).lower()
        if nkw in norm_candidate:
            original = norm_candidate[nkw]
            if original not in relevant_skills:
                relevant_skills.append(original)
            if kw not in keywords_used:
                keywords_used.append(kw)

    if not relevant_skills and student_skills:
        relevant_skills = student_skills[:6]

    projects = context.get("projects", [])
    prioritized_projects = []
    for p in projects:
        desc = (p.get("description", "") + " " + p.get("technologies_used", "") + " " + p.get("project_name", "")).lower()
        relevance_score = sum(1 for kw in job_keywords if kw.lower() in desc)
        prioritized_projects.append((relevance_score, p))
    prioritized_projects.sort(key=lambda x: x[0], reverse=True)
    ordered_projects = [p for _, p in prioritized_projects]

    resume_lines = []
    resume_lines.append(f"# {context['name'].upper()}")
    contact_parts = [p for p in [context['email'], context['phone'], context['location'], context['github_url'], context['linkedin_url']] if p]
    if contact_parts:
        resume_lines.append(" | ".join(contact_parts))
    resume_lines.append("")

    field = context.get("field_of_study") or context.get("degree") or "Computer Science"
    inst = f" at {context['institution']}" if context.get("institution") else ""
    summary = f"Dedicated {field} student{inst} targeting the {target_title} position at {target_company}. Bringing verified practical foundations in {', '.join(relevant_skills[:4]) or 'software development'} with strong analytical problem-solving and disciplined execution."
    resume_lines.append("## PROFESSIONAL SUMMARY")
    resume_lines.append(summary)
    resume_lines.append("")

    resume_lines.append("## TECHNICAL SKILLS")
    if relevant_skills:
        resume_lines.append(f"- **Target Role Skills:** {', '.join(relevant_skills)}")
    other_skills = [s for s in student_skills if s not in relevant_skills]
    if other_skills:
        resume_lines.append(f"- **Additional Demonstrated Skills:** {', '.join(other_skills)}")
    resume_lines.append("")

    if ordered_projects:
        resume_lines.append("## HIGHLIGHTED PROJECTS")
        for p in ordered_projects[:4]:
            p_name = p.get("project_name") or "Key Project"
            p_tech = p.get("technologies_used")
            header = f"### {p_name}" + (f" ({p_tech})" if p_tech else "")
            resume_lines.append(header)
            p_desc = p.get("description") or "Demonstrated end-to-end implementation and testing."
            for line in p_desc.split("\n"):
                clean_l = line.strip().lstrip("-*• ")
                if clean_l:
                    resume_lines.append(f"- {clean_l}")
            resume_lines.append("")

    experience = context.get("experience", [])
    if experience:
        resume_lines.append("## EXPERIENCE")
        for exp in experience:
            role = exp.get("role_title") or exp.get("title") or "Intern / Contributor"
            org = exp.get("organization") or exp.get("company") or ""
            dur = exp.get("duration") or ""
            resume_lines.append(f"### {role}" + (f" - {org}" if org else "") + (f" ({dur})" if dur else ""))
            exp_desc = exp.get("description") or ""
            for line in exp_desc.split("\n"):
                clean_l = line.strip().lstrip("-*• ")
                if clean_l:
                    resume_lines.append(f"- {clean_l}")
            resume_lines.append("")

    education = context.get("education", [])
    if education or context.get("degree"):
        resume_lines.append("## EDUCATION")
        if education:
            for edu in education:
                deg = edu.get("degree") or context.get("degree") or "Bachelor of Science"
                ins = edu.get("institution") or context.get("institution") or ""
                yr = edu.get("year_of_completion") or ""
                resume_lines.append(f"- **{deg}**{f' — {ins}' if ins else ''}{f' ({yr})' if yr else ''}")
        else:
            deg = context.get("degree") or "Degree in Progress"
            ins = context.get("institution") or ""
            resume_lines.append(f"- **{deg}**{f' — {ins}' if ins else ''}")
        resume_lines.append("")

    certs = context.get("certifications", [])
    if certs:
        resume_lines.append("## CERTIFICATIONS")
        for c in certs:
            c_name = c.get("certification_name") if isinstance(c, dict) else str(c)
            resume_lines.append(f"- {c_name}")
        resume_lines.append("")

    tailored_text = "\n".join(resume_lines).strip()

    record = TailoredResume(
        student_id=student.student_id,
        job_id=job.job_id if job and getattr(job, "job_id", None) else None,
        job_title=target_title,
        company=target_company,
        tailored_resume=tailored_text,
        keywords_used=_json(keywords_used),
        relevant_skills=_json(relevant_skills),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "success": True,
        "job_title": target_title,
        "company": target_company,
        "tailored_resume": tailored_text,
        "keywords_used": keywords_used,
        "relevant_skills": relevant_skills,
        "tailored_resume_id": record.tailored_resume_id,
        "created_at": record.created_at,
    }


def generate_cover_letter(db: Session, student: Student, request: CoverLetterRequest) -> dict:
    job = get_job(db, request.job_id) if request.job_id else None
    target_title = request.job_title or (job.title if job else "Intern")
    target_company = request.company or (job.company if job else "Target Company")
    job_desc = request.job_description or (job.description if job else "")
    context = candidate_context(db, student)

    skills = ", ".join(context["skills"][:6]) or "software engineering and problem-solving"
    projects = context["projects"][:2]
    project_names = [p.get("project_name", "key project") for p in projects if isinstance(p, dict)]
    project_text = ", ".join(project_names) if project_names else "my academic coursework and technical projects"

    content = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {target_title} position at {target_company}. As a student of {context.get('field_of_study') or 'Computer Science'}{f" at {context['institution']}" if context.get('institution') else ""}, my academic preparation and hands-on work with {skills} align directly with the needs of your team.

Through {project_text}, I have developed practical experience designing, implementing, and validating software solutions. I focus on writing clear, maintainable code and solving real-world challenges through continuous learning.

I am particularly excited about the work being done at {target_company}. I would welcome the opportunity to bring my background in {skills} to your projects while learning from your experienced engineering team.

Thank you for your time and consideration. I look forward to the possibility of discussing how my skills and background meet your requirements.

Sincerely,
{context['name']}"""

    letter = CoverLetter(
        student_id=student.student_id,
        job_id=job.job_id if job and getattr(job, "job_id", None) else None,
        job_title=target_title,
        company=target_company,
        content=content,
    )
    db.add(letter)
    db.commit()
    db.refresh(letter)
    return {
        "cover_letter_id": letter.cover_letter_id,
        "job_id": letter.job_id,
        "job_title": letter.job_title,
        "company": letter.company,
        "cover_letter": letter.content,
        "created_at": letter.created_at,
        "success": True,
    }


def prepare_interview_questions(db: Session, student: Student, request: InterviewPrepRequest) -> dict:
    job = get_job(db, request.job_id) if request.job_id else None
    target_title = request.job_title or (job.title if job else "Software Engineer Intern")
    target_company = request.company or (job.company if job else "Company")
    context = candidate_context(db, student)

    skills = context.get("skills", [])
    top_skill = skills[0] if skills else "Python"
    second_skill = skills[1] if len(skills) > 1 else "SQL"
    projects = context.get("projects", [])
    project = projects[0].get("project_name", "recent project") if projects else "coursework project"

    technical_q = [
        {
            "question": f"Explain the core architectural principles and best practices when developing applications with {top_skill}.",
            "category": "Technical",
            "difficulty": "Medium",
            "why_this_question_matters": f"Demonstrates technical depth in {top_skill}, a primary skill required for the {target_title} role.",
            "preparation_guidance": f"Review {top_skill} data structures, error handling, performance optimization, and clean code practices.",
        },
        {
            "question": f"How do you design, validate, and test a RESTful API using {second_skill} and backend services?",
            "category": "Technical",
            "difficulty": "Medium",
            "why_this_question_matters": "Evaluates foundational understanding of client-server contracts, HTTP methods, and database integration.",
            "preparation_guidance": "Practice explaining endpoints, HTTP status codes, schema validation, and database queries.",
        },
    ]

    resume_q = [
        {
            "question": f"Walk me through the technical decisions and architecture you selected for {project}.",
            "category": "Resume-Based",
            "difficulty": "Medium",
            "why_this_question_matters": "Validates hands-on ownership and truthfulness of projects claimed on your resume.",
            "preparation_guidance": "Prepare a 2-minute overview: Problem -> Architecture -> Your specific contribution -> Measured outcome.",
        },
    ]

    project_q = [
        {
            "question": f"What was the most challenging bug or technical blocker you encountered in {project}, and how did you resolve it?",
            "category": "Project-Based",
            "difficulty": "Hard",
            "why_this_question_matters": "Assesses problem-solving methodology, debugging capabilities, and persistence under technical blockers.",
            "preparation_guidance": "Structure with the STAR method (Situation, Task, Action, Result). Highlight specific debugging tools used.",
        },
    ]

    role_q = [
        {
            "question": f"Given the responsibilities for {target_title} at {target_company}, which requirement would you ramp up on first, and how?",
            "category": "Role-Specific",
            "difficulty": "Medium",
            "why_this_question_matters": "Checks role comprehension, self-awareness, and proactive learning agility.",
            "preparation_guidance": f"Identify any skill gap relative to {target_company} and outline a structured 30-day learning plan.",
        },
    ]

    hr_q = [
        {
            "question": f"Why are you specifically interested in interning with {target_company}?",
            "category": "HR/Behavioral",
            "difficulty": "Easy",
            "why_this_question_matters": "Tests company alignment, motivation, and professional communication.",
            "preparation_guidance": f"Reference {target_company}'s products or technology and connect your career goals to their mission.",
        },
        {
            "question": "Tell me about a time you had to balance competing deadlines or received constructive feedback.",
            "category": "HR/Behavioral",
            "difficulty": "Medium",
            "why_this_question_matters": "Evaluates coachability, emotional maturity, and teamwork in collaborative environments.",
            "preparation_guidance": "Describe a real situation objectively, focusing on the constructive change you made and the positive outcome.",
        },
    ]

    all_q = technical_q + resume_q + project_q + role_q + hr_q
    return {
        "job_title": target_title,
        "company": target_company,
        "questions": all_q,
        "technical_questions": technical_q,
        "resume_questions": resume_q,
        "project_questions": project_q,
        "role_questions": role_q,
        "hr_questions": hr_q,
    }


def _question_bank(interview_type: str, context: dict, job_description: str = "") -> list[tuple[str, str]]:
    skills = ", ".join(context["skills"][:4]) or "your core skills"
    project = context["projects"][0].get("project_name", "your recent project") if context["projects"] else "your recent project"
    banks = {
        "technical": [
            ("technical", f"Explain a challenging problem you solved using {skills}."),
            ("technical", "How would you design a reliable API for a production application?"),
            ("technical", "How do you test and monitor software before and after deployment?"),
            ("technical", "Explain how you handle data validation and error handling in your code."),
        ],
        "behavioral": [
            ("behavioral", "Tell me about a time you received difficult feedback and how you acted on it."),
            ("behavioral", "Describe a time you had to prioritize competing deadlines."),
            ("behavioral", "Tell me about a collaboration that changed your approach to a problem."),
            ("behavioral", "Give an example of a situation where you had to learn a new tool quickly."),
        ],
        "hr": [
            ("hr", "Why are you interested in this role?"),
            ("hr", "What kind of team helps you do your best work?"),
            ("hr", "What are you hoping to learn next in your career?"),
            ("hr", "Where do you see yourself contributing most in the next 6-12 months?"),
        ],
        "project": [
            ("project", f"Walk me through {project}, including your contribution and the result."),
            ("project", "What tradeoff would you revisit in one of your projects?"),
            ("project", "How did you validate that your project solved the intended problem?"),
            ("project", "How did you choose the technologies and architecture for your project?"),
        ],
        "role-specific": [
            ("role-specific", "Which part of this role is the closest match for your experience?"),
            ("role-specific", "Which requirement would you need to ramp up on first, and how would you do it?"),
            ("role-specific", "How would your current skills contribute to this internship team?"),
            ("role-specific", "How do you keep up with industry trends relevant to this position?"),
        ],
        "job-specific": [
            ("job-specific", "Which part of this job description is the closest match for your experience?"),
            ("job-specific", "Which requirement would you need to ramp up on first, and how would you do it?"),
            ("job-specific", "How would your current skills contribute in this role?"),
        ],
    }
    if interview_type == "mixed":
        mixed = [
            banks["technical"][0],
            banks["project"][0],
            banks["role-specific"][0],
            banks["behavioral"][0],
            banks["hr"][0],
            banks["technical"][1],
            banks["project"][1],
            banks["behavioral"][1],
            banks["role-specific"][1],
            banks["hr"][1],
        ]
        return mixed
    selected = banks.get(interview_type, banks["technical"])
    return selected + [("scenario", "Describe how you would investigate an unfamiliar production failure.")]


def start_interview(db: Session, student: Student, request: Any) -> dict:
    context = candidate_context(db, student)
    questions = _question_bank(request.interview_type, context, request.job_description or "")
    interview = Interview(
        student_id=student.student_id,
        job_id=request.job_id,
        interview_type=request.interview_type,
        difficulty=request.difficulty,
        question_count=request.question_count,
    )
    db.add(interview)
    db.flush()
    for sequence in range(request.question_count):
        category, question = questions[sequence % len(questions)]
        db.add(InterviewQuestion(interview_id=interview.interview_id, sequence=sequence, category=category, question=question))
    db.commit()
    db.refresh(interview)
    first = db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.interview_id, InterviewQuestion.sequence == 0).one()
    return {
        "interview_id": interview.interview_id,
        "status": interview.status,
        "question_number": 1,
        "total_questions": interview.question_count,
        "question": first.question,
        "category": first.category,
    }


def get_owned_interview(db: Session, student: Student, interview_id: int) -> Interview:
    interview = db.query(Interview).filter(Interview.interview_id == interview_id, Interview.student_id == student.student_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


def answer_interview(db: Session, student: Student, interview_id: int, answer: str) -> dict:
    interview = get_owned_interview(db, student, interview_id)
    if interview.status != "active":
        raise HTTPException(status_code=400, detail="Interview is already complete")
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview_id,
        InterviewQuestion.sequence == interview.current_question,
    ).one_or_none()
    if not question:
        raise HTTPException(status_code=400, detail="No unanswered interview question is available")

    words = answer.strip().split()
    word_count = len(words)
    score = min(100, max(25, 40 + min(50, word_count * 2)))

    relevance = "Directly addresses the question asked." if word_count >= 15 else "Partially addresses the question; lacks specific details."
    technical_correctness = "Demonstrates sound technical understanding and proper terminology." if score >= 70 else "Basic concepts present; elaborate on concrete implementation steps."
    completeness = "Covers problem context, action taken, and outcome." if word_count >= 25 else "Answer is concise; include more context on your approach and results."
    communication = "Well structured with clear articulation." if word_count >= 20 else "Keep answer concise but articulate concrete steps."
    missing_points = "Consider specifying measurable metrics and error handling." if score < 85 else "None identified."
    improvement_suggestions = "Use the STAR framework (Situation, Task, Action, Result) to convey quantifiable impact."

    feedback = f"{technical_correctness} {completeness} {improvement_suggestions}"

    question.answer = answer
    question.score = score
    question.feedback = feedback
    interview.current_question += 1

    if interview.current_question >= interview.question_count:
        scores = [item.score or 0 for item in db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview_id).all()]
        interview.status = "completed"
        interview.overall_score = round(sum(scores) / len(scores)) if scores else score

        tech_score = round(interview.overall_score * 0.95)
        comm_score = min(100, round(interview.overall_score * 1.05))

        final_report = {
            "questions_answered": interview.question_count,
            "overall_score": interview.overall_score,
            "technical_score": tech_score,
            "communication_score": comm_score,
            "strengths": [
                "Demonstrated structured logical reasoning",
                "Addressed the core interview questions directly",
                "Clear professional communication",
            ],
            "areas_to_improve": [
                "Incorporate more quantifiable project metrics",
                "Deepen explanation of edge cases and tradeoffs",
            ],
            "weaknesses": [
                "Could provide deeper system-level tradeoff explanations",
            ],
            "technical_topics_to_revise": [
                "System architecture & REST API standards",
                "Unit and integration testing patterns",
                "Concurrency and database query optimization",
            ],
            "project_topics_to_revise": [
                "Clarifying your direct individual contribution vs team",
                "Articulating project performance bottlenecks and resolutions",
            ],
            "hr_preparation": [
                "Practice 2-minute elevator pitch",
                "Prepare 3 insightful questions to ask the interviewer",
            ],
            "recommended_preparation_plan": [
                "Days 1-7: Revise core technical fundamentals and data structures",
                "Days 8-15: Practice explaining projects using STAR framework",
                "Days 16-22: Conduct timed mock coding and API design sessions",
                "Days 23-30: Rehearse behavioral questions and company research",
            ],
            "recommendations": [
                "Practice concise STAR-format answers",
                "Review system architecture fundamentals before technical rounds",
            ],
        }
        interview.report = _json(final_report)
    db.commit()

    return {
        "interview_id": interview_id,
        "question_number": interview.current_question,
        "score": score,
        "feedback": feedback,
        "relevance": relevance,
        "technical_correctness": technical_correctness,
        "completeness": completeness,
        "communication": communication,
        "missing_points": missing_points,
        "improvement_suggestions": improvement_suggestions,
        "next_question_available": interview.status == "active",
    }


def next_interview_question(db: Session, student: Student, interview_id: int) -> dict:
    interview = get_owned_interview(db, student, interview_id)
    if interview.status != "active":
        raise HTTPException(status_code=400, detail="Interview is complete")
    question = db.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview_id, InterviewQuestion.sequence == interview.current_question).one()
    return {
        "interview_id": interview_id,
        "status": interview.status,
        "question_number": interview.current_question + 1,
        "total_questions": interview.question_count,
        "question": question.question,
        "category": question.category,
    }


def interview_result(db: Session, student: Student, interview_id: int) -> dict:
    interview = get_owned_interview(db, student, interview_id)
    report = _load(interview.report, {})
    return {
        "interview_id": interview_id,
        "status": interview.status,
        "overall_score": interview.overall_score,
        "technical_score": report.get("technical_score", interview.overall_score),
        "communication_score": report.get("communication_score", interview.overall_score),
        "questions_answered": report.get("questions_answered", interview.question_count),
        "strengths": report.get("strengths", ["Structured logical reasoning"]),
        "weaknesses": report.get("weaknesses", ["Add more quantifiable impact"]),
        "areas_to_improve": report.get("areas_to_improve", ["Incorporate more quantifiable project metrics"]),
        "technical_topics_to_revise": report.get("technical_topics_to_revise", ["System architecture & API design"]),
        "project_topics_to_revise": report.get("project_topics_to_revise", ["STAR project walkthrough"]),
        "hr_preparation": report.get("hr_preparation", ["Prepare questions for the interviewer"]),
        "recommended_preparation_plan": report.get("recommended_preparation_plan", [
            "Week 1: Technical fundamentals",
            "Week 2: Project walkthroughs",
            "Week 3: Timed mock answers",
            "Week 4: Final preparation",
        ]),
        "recommendations": report.get("recommendations", ["Practice concise STAR-format answers"]),
        "report": report,
    }


def interview_detail(db: Session, student: Student, interview_id: int) -> dict:
    interview = get_owned_interview(db, student, interview_id)
    result = interview_result(db, student, interview_id)
    return {
        **result,
        "interview_type": interview.interview_type,
        "difficulty": interview.difficulty,
        "question_count": interview.question_count,
        "current_question": interview.current_question,
        "created_at": interview.created_at,
    }


def chat_career_assistant(db: Session, student: Student, message: str, job_id: Optional[int] = None) -> dict:
    lower = message.lower()
    context = candidate_context(db, student)
    student_skills = context.get("skills", [])
    top_skills_str = ", ".join(student_skills[:5]) or "Python, software development"

    job = get_job(db, job_id) if job_id else None
    if not job:
        latest_report = db.query(SkillGapReport).filter(SkillGapReport.student_id == student.student_id).order_by(SkillGapReport.created_at.desc()).first()
        if latest_report and latest_report.job_id:
            job = db.query(Job).filter(Job.job_id == latest_report.job_id).first()

    context_used = ["student_profile"]

    if any(q in lower for q in ("which internships", "match my skills", "what jobs match", "recommended jobs")):
        routed_agent = "job_resume_matching"
        context_used.append("job_matching")
        all_jobs = db.query(Job).limit(5).all()
        job_titles = [f"• **{j.title}** at {j.company} (Requires: {', '.join(_load(j.required_skills)[:3])})" for j in all_jobs]
        jobs_list = "\n".join(job_titles) if job_titles else "No internships found in the database yet."
        response = f"Based on your profile skills ({top_skills_str}), here are matching internships:\n\n{jobs_list}\n\nYou can run a detailed match on the Jobs page."
        suggestions = ["Why is this internship a good match for my profile?", "What skills am I missing?", "How should I prepare for this interview?"]

    elif any(q in lower for q in ("why is this", "good match", "match for my profile")):
        routed_agent = "job_resume_matching"
        if job:
            context_used.append("selected_job")
            req = _load(job.required_skills)
            matched = [s for s in req if s.lower() in [cs.lower() for cs in student_skills]]
            response = f"**{job.title} at {job.company}** is a strong match because you demonstrate verified proficiency in **{', '.join(matched) if matched else top_skills_str}**. These directly align with their core requirements."
        else:
            response = f"Your demonstrated skills in **{top_skills_str}** provide a solid foundation for software and AI internships. Select a job to view exact match breakdowns."
        suggestions = ["What skills am I missing?", "How can I improve my resume for this job?", "Generate a cover letter for this role."]

    elif any(q in lower for q in ("missing", "skill am i missing", "skill gap", "skills am i missing", "what skills should i learn", "what should i learn")):
        routed_agent = "skill_gap"
        context_used.append("skill_gap")
        report = db.query(SkillGapReport).filter(SkillGapReport.student_id == student.student_id).order_by(SkillGapReport.created_at.desc()).first()
        if report:
            stored = _load(report.gaps, {})
            missing = stored.get("missing_skills", []) if isinstance(stored, dict) else []
            if missing:
                response = f"Your latest Skill Gap Analysis for **{report.target_role or 'your target role'}** identifies these missing critical skills:\n" + "\n".join(f"• **{s}**" for s in missing[:4]) + "\n\nI recommend prioritizing these in your learning roadmap."
            else:
                response = "You have matched all core required skills in your latest analysis! Focus on preferred skills and project demonstrations."
        else:
            if job:
                req = _load(job.required_skills)
                missing = [s for s in req if s.lower() not in [cs.lower() for cs in student_skills]]
                response = f"For **{job.title} at {job.company}**, your missing skills are: {', '.join(missing) if missing else 'None! You match the required skills.'}."
            else:
                response = "Run Skill Gap Analysis with a target role to receive prioritized missing skills and learning paths."
        suggestions = ["Give me a 30-day preparation plan.", "How can I improve my resume for this job?", "How should I prepare for this interview?"]

    elif any(q in lower for q in ("improve my resume", "resume for this job", "tailor resume", "resume advice")):
        routed_agent = "resume"
        context_used.extend(["student_profile", "resume_customization"])
        role_name = job.title if job else "your target internship"
        response = f"To optimize your resume for **{role_name}**:\n1. **Highlight Matching Skills**: Place {top_skills_str} prominently near the top.\n2. **Align Project Bullet Points**: Frame your project achievements with active action verbs and measurable outcomes.\n3. **Incorporate Job Keywords**: Ensure terminology matches the job description.\n4. **Keep It Factual**: Never invent skills; only emphasize your verified accomplishments."
        suggestions = ["Generate a tailored resume.", "Generate a cover letter for this role.", "How should I prepare for this interview?"]

    elif any(q in lower for q in ("cover letter", "coverletter")):
        routed_agent = "cover_letter"
        context_used.append("cover_letter")
        if job:
            response = f"I can generate a tailored cover letter for **{job.title} at {job.company}** highlighting your verified work with {top_skills_str}. Navigate to the Cover Letter page or request generation directly."
        else:
            response = "Select a target internship, and I will generate a personalized cover letter highlighting your verified skills and projects."
        suggestions = ["Which internships match my skills?", "What skills am I missing?", "What should I do next?"]

    elif any(q in lower for q in ("prepare for this interview", "interview prep", "questions can i expect", "expect")):
        routed_agent = "interview"
        context_used.append("interview_prep")
        role_name = job.title if job else "software engineering internships"
        response = f"For **{role_name}**, expect three main categories of questions:\n1. **Technical**: Deep dive into {top_skills_str} and system design.\n2. **Project-Based**: Step-by-step walkthrough of your portfolio projects using STAR.\n3. **Behavioral / HR**: Collaboration, conflict resolution, and why you want to join.\n\nYou can launch an interactive Mock Interview on the Interview page!"
        suggestions = ["Give me a 30-day preparation plan.", "What skills am I missing?", "What should I do next?"]

    elif any(q in lower for q in ("30-day", "preparation plan", "prep plan", "roadmap", "plan")):
        routed_agent = "skill_gap"
        context_used.extend(["student_profile", "skill_gap"])
        response = """Here is your **30-Day Internship Preparation Plan**:
• **Week 1 (Days 1–7) — Core Fundamentals:** Review foundational data structures, algorithms, and primary language syntax.
• **Week 2 (Days 8–15) — Bridge Skill Gaps:** Build a focused mini-project addressing the top missing technical skill.
• **Week 3 (Days 16–22) — Application Polish:** Tailor your resume and cover letter for target roles; publish project code to GitHub.
• **Week 4 (Days 23–30) — Mock Interviews:** Practice timed technical and behavioral questions using our AI Interviewer."""
        suggestions = ["How should I prepare for this interview?", "What skills am I missing?", "Which internships match my skills?"]

    elif any(q in lower for q in ("what should i do next", "next steps", "what next")):
        routed_agent = "career_assistant"
        response = f"**Recommended Next Steps:**\n1. Review your **Skill Gap Analysis** to identify missing critical skills.\n2. Use **Resume Customizer** to tailor your resume for your target role.\n3. Generate a personalized **Cover Letter**.\n4. Complete an interactive **Mock Interview** to test your readiness."
        suggestions = ["Which internships match my skills?", "What skills am I missing?", "Give me a 30-day preparation plan."]

    else:
        from app.services.agent_orchestrator import route_request
        routed_agent, base_resp = route_request(db, student, message)
        response = base_resp
        suggestions = ["Which internships match my skills?", "What skills am I missing?", "Give me a 30-day preparation plan."]

    return {
        "response": response,
        "context_used": context_used,
        "suggestions": suggestions,
        "routed_agent": routed_agent,
    }


def route_career_message(db: Session, student: Student, message: str) -> tuple[str, str]:
    result = chat_career_assistant(db, student, message)
    return result["routed_agent"], result["response"]

