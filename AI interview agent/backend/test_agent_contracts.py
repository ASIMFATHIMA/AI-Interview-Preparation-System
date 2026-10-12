import pytest
from pydantic import ValidationError

from app.schemas.agent import AGENT_RESPONSIBILITIES, AgentName, get_agent_responsibility
from app.schemas.candidate_profile import CandidateProfileContext


def test_all_career_agents_have_explicit_responsibilities():
    assert {item.name for item in AGENT_RESPONSIBILITIES} == set(AgentName)
    assert all(item.inputs and item.outputs and item.owns for item in AGENT_RESPONSIBILITIES)
    assert get_agent_responsibility(AgentName.INTERVIEW).name == AgentName.INTERVIEW


def test_candidate_profile_context_is_credential_free():
    profile = CandidateProfileContext(
        student_id=1,
        name="Asha Raman",
        email="asha@example.com",
        skills=["Python"],
        preferences={"target_roles": ["Backend Engineer"]},
    )

    assert profile.preferences.target_roles == ["Backend Engineer"]
    with pytest.raises(ValidationError):
        CandidateProfileContext(
            student_id=1,
            name="Asha Raman",
            email="asha@example.com",
            password_hash="must never enter agent context",
        )