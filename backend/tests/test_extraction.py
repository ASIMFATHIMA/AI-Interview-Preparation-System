"""
M1.4 requirement: "Test extraction on several sample resumes."

Run directly (requires ANTHROPIC_API_KEY set in your environment / .env):

    cd backend
    python -m tests.test_extraction

This exercises the full parsing pipeline (text extraction + LLM structured extraction)
against every sample resume in sample_resumes/, without needing the API server running.

It can also be run under pytest, but since it calls the live Claude API it is marked
to skip automatically if no API key is configured (so CI/basic `pytest` runs stay green).
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.resume_parser import extract_text
from app.llm_extractor import extract_structured_resume
from app.config import settings

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_resumes")


def _sample_files():
    return sorted(glob.glob(os.path.join(SAMPLE_DIR, "*.txt")))


requires_api_key = pytest.mark.skipif(
    not settings.ANTHROPIC_API_KEY, reason="ANTHROPIC_API_KEY not set; skipping live LLM test."
)


@requires_api_key
@pytest.mark.parametrize("filepath", _sample_files())
def test_extraction_on_sample_resume(filepath):
    raw_text = extract_text(filepath)
    assert raw_text.strip(), f"No text extracted from {filepath}"

    result = extract_structured_resume(raw_text)

    # Basic sanity checks — every sample resume has at least one skill and one education entry
    assert len(result.skills) > 0, f"No skills extracted from {filepath}"
    assert len(result.education) > 0, f"No education extracted from {filepath}"


def _run_as_script():
    print(f"Using model: {settings.ANTHROPIC_MODEL}\n")
    for filepath in _sample_files():
        print("=" * 80)
        print(f"File: {os.path.basename(filepath)}")
        print("=" * 80)

        raw_text = extract_text(filepath)
        result = extract_structured_resume(raw_text)

        print(json.dumps(result.model_dump(), indent=2))
        print(f"\nExtracted: {len(result.skills)} skills, {len(result.education)} education "
              f"entries, {len(result.experience)} experience entries, "
              f"{len(result.projects)} projects.\n")


if __name__ == "__main__":
    if not settings.ANTHROPIC_API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY (in .env or environment) before running this script.")
        sys.exit(1)
    _run_as_script()
