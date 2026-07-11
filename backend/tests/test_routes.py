from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ── Input validation ──────────────────────────────────────────────────────────

def test_triage_rejects_non_numeric_pincode():
    resp = client.post("/api/triage", json={"pincode": "abc123"})

    assert resp.status_code == 422


def test_triage_rejects_short_pincode():
    resp = client.post("/api/triage", json={"pincode": "1234"})

    assert resp.status_code == 422


def test_relief_rejects_empty_description():
    resp = client.post("/api/relief", json={"description": "   "})

    assert resp.status_code == 422


def test_relief_caps_description_at_1000_chars(valid_gemini_response):
    long_description = "x" * 5000
    with patch(
        "backend.api.routes.match_schemes",
        new=AsyncMock(return_value=valid_gemini_response),
    ) as mock_relief:
        resp = client.post("/api/relief", json={"description": long_description})

    assert resp.status_code == 200
    sent_description = mock_relief.await_args.args[0]
    assert len(sent_description) == 1000


def test_reports_rejects_invalid_pincode():
    resp = client.get("/api/reports/12ab56")

    assert resp.status_code == 422


def test_alert_rejects_invalid_pincode():
    resp = client.get("/api/alert?pincode=notapin")

    assert resp.status_code == 422


# ── Happy paths (boundaries mocked) ───────────────────────────────────────────

def test_reports_returns_firestore_results(sample_reports):
    with patch("backend.api.routes.get_reports", return_value=sample_reports):
        resp = client.get("/api/reports/682001")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["reports"]) == 2
    assert body["reports"][0]["pincode"] == "682001"


def test_triage_streams_sse_with_done_marker(valid_gemini_response):
    with patch(
        "backend.api.routes.synthesize_triage",
        new=AsyncMock(return_value=valid_gemini_response),
    ):
        resp = client.post("/api/triage", json={"pincode": "682001"})

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "data: [DONE]" in resp.text
    assert '"done": true' in resp.text


def test_relief_streams_sse_stages_in_order(valid_gemini_response):
    with patch(
        "backend.api.routes.match_schemes",
        new=AsyncMock(return_value=valid_gemini_response),
    ):
        resp = client.post(
            "/api/relief",
            json={"description": "flood damaged my shop", "language": "Tamil"},
        )

    assert resp.status_code == 200
    body = resp.text
    reading = body.index("Reading your description")
    matching = body.index("Matching schemes")
    complete = body.index("Complete")
    assert reading < matching < complete


def test_health_reports_error_when_gemini_down():
    with (
        patch(
            "backend.api.routes.call_gemini",
            new=AsyncMock(side_effect=RuntimeError("quota exhausted")),
        ),
        patch("backend.api.routes.ping_firestore", return_value=True),
    ):
        resp = client.get("/api/health")

    assert resp.status_code == 200
    assert resp.json() == {"gemini": "error", "firestore": "ok"}


def test_health_ok_when_both_services_up():
    with (
        patch(
            "backend.api.routes.call_gemini",
            new=AsyncMock(return_value={"status": "ok"}),
        ),
        patch("backend.api.routes.ping_firestore", return_value=True),
    ):
        resp = client.get("/api/health")

    assert resp.json() == {"gemini": "ok", "firestore": "ok"}
