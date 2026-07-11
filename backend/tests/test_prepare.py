import asyncio
from unittest.mock import AsyncMock, patch

from backend.agents.prepare import HouseholdProfile, generate_plan
from backend.agents.vulnerability import get_risk_tier


def _profile(pincode: str, language: str = "English") -> HouseholdProfile:
    return HouseholdProfile(
        pincode=pincode,
        floor="ground floor",
        dependents="2 children",
        transport="two-wheeler",
        language=language,
        hours_until_event=48,
    )


def test_generate_plan_injects_profile_into_prompt(valid_gemini_response):
    risk = get_risk_tier("682001")
    with patch(
        "backend.agents.prepare.call_gemini",
        new=AsyncMock(return_value=valid_gemini_response),
    ) as mock_gemini:
        result = asyncio.run(generate_plan(_profile("682001", "Kannada"), risk))

    system_prompt = mock_gemini.await_args.args[0]
    # Plan must be personalized — profile fields drive the output
    assert "ground floor" in system_prompt
    assert "2 children" in system_prompt
    assert "Kannada" in system_prompt
    assert result["response_text"] == valid_gemini_response["response_text"]


def test_generate_plan_second_call_hits_cache(valid_gemini_response):
    risk = get_risk_tier("781001")
    profile = _profile("781001", "Hindi")
    with patch(
        "backend.agents.prepare.call_gemini",
        new=AsyncMock(return_value=valid_gemini_response),
    ) as mock_gemini:
        asyncio.run(generate_plan(profile, risk))
        asyncio.run(generate_plan(profile, risk))

    # Second call served from TTLCache — Gemini spend halved for repeat asks
    assert mock_gemini.await_count == 1


def test_generate_plan_high_risk_allows_more_words(valid_gemini_response):
    risk = get_risk_tier("400001")  # Mumbai — HIGH
    with patch(
        "backend.agents.prepare.call_gemini",
        new=AsyncMock(return_value=valid_gemini_response),
    ) as mock_gemini:
        asyncio.run(generate_plan(_profile("400001", "Marathi"), risk))

    system_prompt = mock_gemini.await_args.args[0]
    assert "200" in system_prompt  # HIGH tier budget, not the 150 default
