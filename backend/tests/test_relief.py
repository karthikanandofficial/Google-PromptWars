import asyncio
from unittest.mock import AsyncMock, patch

from backend.agents.relief import match_schemes, _load_schemes


def test_load_schemes_returns_formatted_rules():
    text = _load_schemes()

    assert "SCHEME:" in text
    assert "Eligibility:" in text
    assert "Documents:" in text


def test_load_schemes_is_cached_between_calls():
    first = _load_schemes()
    second = _load_schemes()

    assert first is second  # module-level cache — file read once


def test_match_schemes_passes_scheme_rules_to_gemini(valid_gemini_response):
    with patch(
        "backend.agents.relief.call_gemini",
        new=AsyncMock(return_value=valid_gemini_response),
    ) as mock_gemini:
        result = asyncio.run(match_schemes("my house was destroyed by flood", "English"))

    system_prompt = mock_gemini.await_args.args[0]
    assert "SCHEME:" in system_prompt  # rules injected as context
    assert result["response_text"] == valid_gemini_response["response_text"]


def test_match_schemes_output_passes_reviewer_validation():
    # Gemini returns a partial dict — reviewer must repair it, not crash
    with patch(
        "backend.agents.relief.call_gemini",
        new=AsyncMock(return_value={"response_text": "SDRF matched"}),
    ):
        result = asyncio.run(match_schemes("crop losses", "Hindi"))

    assert result["phase"] == "AFTER"
    assert "confidence" in result
    assert "metadata" in result
