"""
Resume Parsing Module — Stage 2: structured extraction via LLM.

Takes raw resume text and asks Claude to return strict JSON matching the
ExtractedResume schema (schemas.py). This is what turns an unstructured resume
into the structured Candidate Profile that every future agent will consume.
"""
import json
import re

from anthropic import Anthropic

from .config import settings
from .schemas import ExtractedResume

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """You are a precise resume-parsing engine.
You will be given the raw extracted text of a resume (formatting/whitespace may be imperfect
because it came from a PDF/DOCX text extractor).

Return ONLY a single JSON object — no markdown fences, no commentary, no preamble — matching
exactly this shape:

{
  "summary": "2-3 sentence professional summary of the candidate, written in third person",
  "skills": [
    {"name": "Python", "category": "language", "proficiency": "advanced"}
  ],
  "education": [
    {"institution": "...", "degree": "...", "field": "...", "start_date": "...", "end_date": "...", "gpa": "..."}
  ],
  "experience": [
    {"company": "...", "title": "...", "start_date": "...", "end_date": "...", "description": "..."}
  ],
  "projects": [
    {"name": "...", "description": "...", "technologies": "comma-separated string", "link": "..."}
  ]
}

Rules:
- If a field is not present in the resume, use null (for scalars) or an empty list (for arrays)
  rather than guessing or inventing content.
- category for skills should be one of: "language", "framework", "tool", "database", "cloud",
  "soft-skill", "other" — pick the closest fit.
- proficiency should be one of: "beginner", "intermediate", "advanced" if inferable, otherwise null.
- Dates should be kept as they appear in the resume (e.g. "Jun 2023", "2021", "Present").
- Do not include any text outside the single JSON object.
"""


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_structured_resume(raw_text: str) -> ExtractedResume:
    """
    Calls the Claude API with the raw resume text and returns a validated
    ExtractedResume object. Raises ValueError if the model's output doesn't
    parse/validate as JSON matching the schema.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Cannot extract structured data from empty resume text.")

    client = _get_client()

    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Resume text:\n\n{raw_text}",
            }
        ],
    )

    text_blocks = [block.text for block in response.content if block.type == "text"]
    raw_output = "\n".join(text_blocks)
    cleaned = _strip_json_fences(raw_output)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}\nRaw output: {raw_output[:500]}")

    return ExtractedResume.model_validate(data)
