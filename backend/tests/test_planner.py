import asyncio
from unittest.mock import AsyncMock, patch

from backend.agents.planner import (
    detect_intent,
    route,
    _missing_profile_fields,
    _parse_language,
    _parse_pincode,
    _risk_greeting,
)


# ── Intent detection ──────────────────────────────────────────────────────────

def test_detect_intent_prepare_keyword_returns_prepare():
    assert detect_intent("help me prepare for the monsoon") == "PREPARE"


def test_detect_intent_alert_keyword_returns_alert():
    assert detect_intent("any weather warning today?") == "ALERT"


def test_detect_intent_relief_keyword_returns_relief():
    assert detect_intent("how do I claim compensation for my losses") == "RELIEF"


def test_detect_intent_coord_keyword_returns_coord():
    assert detect_intent("give me the triage brief") == "COORD"


def test_detect_intent_hindi_keyword_returns_report():
    assert detect_intent("यहाँ पानी भर गया है") == "REPORT"


def test_detect_intent_unrelated_text_returns_none():
    assert detect_intent("hello there") is None


# ── Language parsing ──────────────────────────────────────────────────────────

def test_parse_language_by_name():
    assert _parse_language("Malayalam") == "Malayalam"


def test_parse_language_by_number():
    assert _parse_language("2") == "Hindi"


def test_parse_language_native_script():
    assert _parse_language("தமிழ்") == "Tamil"


def test_parse_language_unknown_defaults_to_english():
    assert _parse_language("klingon") == "English"


# ── Pincode parsing ───────────────────────────────────────────────────────────

def test_parse_pincode_extracts_six_digits():
    assert _parse_pincode("my pincode is 682001 thanks") == "682001"


def test_parse_pincode_rejects_short_number():
    assert _parse_pincode("12345") is None


def test_parse_pincode_rejects_no_digits():
    assert _parse_pincode("kochi") is None


# ── Profile helpers ───────────────────────────────────────────────────────────

def test_missing_profile_fields_all_empty():
    assert _missing_profile_fields({}) == ["floor", "dependents", "transport"]


def test_missing_profile_fields_partial():
    session = {"floor": "2nd", "dependents": "", "transport": "bike"}
    assert _missing_profile_fields(session) == ["dependents"]


def test_risk_greeting_mentions_tier():
    assert "HIGH" in _risk_greeting("HIGH", "English")
    assert "LOW" in _risk_greeting("LOW", "English")


# ── Routing (state machine) ───────────────────────────────────────────────────

def test_route_await_pincode_invalid_input_reprompts():
    session = {"state": "AWAIT_PINCODE", "language": "English"}

    text, updated = asyncio.run(route(session, "not a pincode", "hash1"))

    assert "6-digit" in text
    assert updated["state"] == "AWAIT_PINCODE"  # state unchanged


def test_route_await_pincode_valid_transitions_to_ready():
    session = {"state": "AWAIT_PINCODE", "language": "English"}

    text, updated = asyncio.run(route(session, "682001", "hash1"))

    assert updated["state"] == "READY"
    assert updated["pincode"] == "682001"
    assert "HIGH" in text  # Ernakulam is HIGH risk in NDMA data


def test_route_ready_unknown_text_returns_help_menu():
    session = {"state": "READY", "language": "English", "pincode": "682001"}

    text, _ = asyncio.run(route(session, "xyzzy", "hash1"))

    assert "PREPARE" in text and "ALERT" in text


def test_route_ready_alert_intent_calls_alert_agent(valid_gemini_response):
    session = {"state": "READY", "language": "Malayalam", "pincode": "682001"}
    with patch(
        "backend.agents.planner.get_alert",
        new=AsyncMock(return_value=valid_gemini_response),
    ) as mock_alert:
        text, updated = asyncio.run(route(session, "any weather alert?", "hash1"))

    mock_alert.assert_awaited_once_with("682001", "Malayalam")
    assert text == valid_gemini_response["response_text"]
    assert updated["last_intent"] == "ALERT"


def test_route_ready_relief_intent_calls_relief_agent(valid_gemini_response):
    session = {"state": "READY", "language": "English", "pincode": "400001"}
    with patch(
        "backend.agents.planner.match_schemes",
        new=AsyncMock(return_value=valid_gemini_response),
    ) as mock_relief:
        text, updated = asyncio.run(route(session, "I lost my house, need compensation", "hash1"))

    mock_relief.assert_awaited_once()
    assert updated["last_intent"] == "RELIEF"
