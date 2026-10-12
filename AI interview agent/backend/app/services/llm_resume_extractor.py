import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY) if API_KEY else None


def extract_resume_information(resume_text: str) -> dict:

    if not client:
        return fallback_extraction(resume_text)

    prompt = f"""
You are an expert resume parser.

Analyze the following resume and extract structured information.

Return ONLY valid JSON.

Required JSON structure:

{{
    "summary": "",
    "skills": [],
    "education": [],
    "experience": [],
    "projects": [],
    "certifications": [],
    "achievements": []
}}

Rules:

1. Do not invent information.
2. Only extract information present in the resume.
3. Skills must be returned as a list of strings.
4. Education must contain degree, institution, field, year if available.
5. Experience must contain company, role, duration and description if available.
6. Projects must contain project name, technologies and description.
7. Certifications must contain certification name and organization if available.
8. Achievements must contain only achievements mentioned in the resume.
9. If information is unavailable, return an empty list or empty string.

Resume:

{resume_text}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        result = response.text.strip()

        # Remove markdown JSON fences if Gemini returns them
        if result.startswith("```json"):
            result = result[7:]

        if result.startswith("```"):
            result = result[3:]

        if result.endswith("```"):
            result = result[:-3]

        result = result.strip()

        return json.loads(result)

    except Exception as error:

        print("LLM extraction failed:", error)

        return fallback_extraction(resume_text)


def fallback_extraction(text: str) -> dict:
    """
    Basic fallback parser.
    This allows the application to work even if
    Gemini API is unavailable.
    """

    skills = []

    known_skills = [
        "Python",
        "Java",
        "JavaScript",
        "C",
        "C++",
        "SQL",
        "MySQL",
        "PostgreSQL",
        "MongoDB",
        "Django",
        "Flask",
        "FastAPI",
        "React",
        "Node.js",
        "Machine Learning",
        "Deep Learning",
        "Artificial Intelligence",
        "Generative AI",
        "LLM",
        "RAG",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "TensorFlow",
        "PyTorch",
        "Git",
        "Docker",
        "AWS"
    ]

    lower_text = text.lower()

    for skill in known_skills:

        if skill.lower() in lower_text:
            skills.append(skill)

    return {
        "summary": "",
        "skills": skills,
        "education": extract_section(text, [
            "education",
            "academic qualification"
        ]),
        "experience": extract_section(text, [
            "experience",
            "work experience",
            "internship"
        ]),
        "projects": extract_section(text, [
            "projects",
            "academic projects"
        ]),
        "certifications": extract_section(text, [
            "certifications",
            "certificates"
        ]),
        "achievements": extract_section(text, [
            "achievements",
            "awards"
        ])
    }


def extract_section(text: str, section_names: list):

    lines = text.splitlines()

    found = []

    active = False

    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            continue

        lower_line = clean_line.lower()

        if any(section in lower_line for section in section_names):
            active = True
            continue

        if active:
            found.append(clean_line)

    return found[:30]