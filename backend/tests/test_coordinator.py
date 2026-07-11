import asyncio
from unittest.mock import AsyncMock, patch

from backend.agents.coordinator import synthesize_triage


def test_no_reports_returns_certain_empty_brief():
    with patch("backend.agents.coordinator.get_reports", return_value=[]):
        result = asyncio.run(synthesize_triage("560001"))

    assert result["confidence"] == 1.0
    assert "560001" in result["response_text"]
    assert result["phase"] == "COORD"


def test_reports_are_aggregated_into_gemini_prompt(sample_reports, valid_gemini_response):
    with (
        patch("backend.agents.coordinator.get_reports", return_value=sample_reports),
        patch(
            "backend.agents.coordinator.call_gemini",
            new=AsyncMock(return_value=valid_gemini_response),
        ) as mock_gemini,
    ):
        result = asyncio.run(synthesize_triage("682001", hours=6))

    system_prompt = mock_gemini.await_args.args[0]
    # Every report's text must reach the model — triage is only real if it
    # reflects actual citizen input
    assert "knee level" in system_prompt
    assert "Periyar river" in system_prompt
    assert result["response_text"] == valid_gemini_response["response_text"]


def test_report_count_included_in_user_message(sample_reports, valid_gemini_response):
    with (
        patch("backend.agents.coordinator.get_reports", return_value=sample_reports),
        patch(
            "backend.agents.coordinator.call_gemini",
            new=AsyncMock(return_value=valid_gemini_response),
        ) as mock_gemini,
    ):
        asyncio.run(synthesize_triage("682001"))

    user_msg = mock_gemini.await_args.args[1]
    assert "2 citizen reports" in user_msg
