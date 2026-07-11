import asyncio
from unittest.mock import patch

from backend.services.imd import fetch_imd_alert, _extract_relevant_text, _get_fallback_alert


# ── Fallback data ─────────────────────────────────────────────────────────────

def test_fallback_alert_known_prefix_returns_district_alert():
    result = _get_fallback_alert("682")

    assert result["source"] == "fallback"
    assert result["headline"]
    assert result["detail"]


def test_fallback_alert_unknown_prefix_returns_generic_advisory():
    result = _get_fallback_alert("999")

    assert result["source"] == "fallback"
    assert result["alert_level"] == "Yellow"
    assert "rainfall" in result["detail"].lower()


# ── HTML extraction ───────────────────────────────────────────────────────────

def test_extract_relevant_text_finds_state_line():
    html = (
        "<html><body>"
        "<p>Heavy to very heavy rainfall warning issued for Kerala coastal districts today.</p><br>"
        "<p>Delhi remains dry.</p>"
        "</body></html>"
    )

    result = _extract_relevant_text(html, "682001")

    assert "Kerala" in result


def test_extract_relevant_text_unknown_prefix_returns_empty():
    html = "<p>Heavy rainfall warning for Kerala.</p>"

    assert _extract_relevant_text(html, "999999") == ""


def test_extract_relevant_text_strips_html_tags():
    html = "<b>Orange alert for Maharashtra: extremely heavy rainfall expected in Mumbai.</b>"

    result = _extract_relevant_text(html, "400001")

    assert "<b>" not in result
    assert "Maharashtra" in result


# ── Live fetch with network failure ───────────────────────────────────────────

def test_fetch_falls_back_when_network_unavailable():
    # Simulate total network failure — client construction raises
    with patch(
        "backend.services.imd.httpx.AsyncClient",
        side_effect=ConnectionError("network down"),
    ):
        result = asyncio.run(fetch_imd_alert("682001"))

    assert result["source"] == "fallback"
    assert result["detail"]  # never empty — user always gets guidance
