from fastapi.testclient import TestClient

from backend.api.webhook import _hash_phone, _sanitize_body, _twiml
from backend.main import app

client = TestClient(app)


# ── Phone hashing ─────────────────────────────────────────────────────────────

def test_hash_phone_is_deterministic():
    assert _hash_phone("+919876543210") == _hash_phone("+919876543210")


def test_hash_phone_produces_sha256_hex():
    result = _hash_phone("+919876543210")

    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_hash_phone_never_contains_plaintext_number():
    assert "9876543210" not in _hash_phone("+919876543210")


# ── Input sanitization ────────────────────────────────────────────────────────

def test_sanitize_strips_html_tags():
    assert _sanitize_body("<script>alert(1)</script>water rising") == "alert(1)water rising"


def test_sanitize_truncates_to_500_chars():
    assert len(_sanitize_body("a" * 2000)) == 500


def test_sanitize_unescapes_entities_then_strips():
    result = _sanitize_body("&lt;b&gt;flood&lt;/b&gt; near bridge")

    assert "<b>" not in result
    assert "flood" in result


def test_sanitize_empty_input_returns_empty():
    assert _sanitize_body("   ") == ""


# ── TwiML output ──────────────────────────────────────────────────────────────

def test_twiml_escapes_xml_special_chars():
    resp = _twiml("water > 2ft & rising <fast>")

    body = resp.body.decode()
    assert "<fast>" not in body
    assert "&lt;fast&gt;" in body
    assert body.startswith("<?xml")


# ── Signature validation ──────────────────────────────────────────────────────

def test_webhook_rejects_missing_signature():
    resp = client.post(
        "/webhook",
        data={"From": "whatsapp:+919876543210", "Body": "HI"},
    )

    assert resp.status_code == 403


def test_webhook_rejects_forged_signature():
    resp = client.post(
        "/webhook",
        data={"From": "whatsapp:+919876543210", "Body": "HI"},
        headers={"X-Twilio-Signature": "forged-signature-value"},
    )

    assert resp.status_code == 403
