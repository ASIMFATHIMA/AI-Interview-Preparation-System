"""Centralized Ollama LLM Service for TinyLlama.

Provides unified text generation for all Milestone 3 agents:
- Skill Gap Analysis Agent
- Resume and Cover Letter Customization Agent
- Interview Preparation Agent
- Conversational Career Assistant

Includes strict hallucination prevention guardrails and fallback when Ollama is busy or offline.
"""

import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "45"))

STRICT_ANTI_HALLUCINATION_SYSTEM_PROMPT = """You are an accurate, truthful AI Career Companion Agent.
CRITICAL HALLUCINATION PREVENTION RULES:
1. USE ONLY THE PROVIDED CANDIDATE DATA AND JOB INFORMATION.
2. NEVER invent or assume skills, experience, projects, companies, certifications, job titles, or education.
3. If information is unavailable in the profile, state: "Information not available in the provided profile."
4. For missing skills: The skill must remain a GAP. Never claim or add a missing skill to a candidate's resume.
5. Provide grounded, factual, actionable guidance directly relevant to the internship role.
"""


def _ollama_available() -> bool:
    """Check whether the Ollama server is reachable."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def is_available() -> bool:
    """Public helper to check Ollama availability."""
    return _ollama_available()


def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
    temperature: float = 0.3,
    extra_options: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Generate text using Ollama TinyLlama.

    Returns the model's generated text output, or None if Ollama is unavailable/fails.
    """
    use_model = model or OLLAMA_MODEL
    use_timeout = timeout or OLLAMA_TIMEOUT
    options: Dict[str, Any] = {"temperature": temperature}
    if extra_options:
        options.update(extra_options)

    payload: Dict[str, Any] = {
        "model": use_model,
        "prompt": prompt,
        "system": system_prompt or STRICT_ANTI_HALLUCINATION_SYSTEM_PROMPT,
        "stream": False,
        "options": options,
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=use_timeout,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        result = (data.get("response") or "").strip()
        return result or None
    except Exception:
        return None