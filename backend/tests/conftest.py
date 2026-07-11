"""Shared fixtures. Sets fake env vars before backend.config import so the
suite runs on CI machines with no .env file present."""
import os

# Must be set before any backend import — config.Settings() fails fast otherwise
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-twilio-token")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "test-twilio-sid")
os.environ.setdefault("FIREBASE_CREDENTIALS_PATH", "Firebase.json")

import pytest


@pytest.fixture
def valid_gemini_response() -> dict:
    """A fully schema-compliant Gemini response, as the reviewer expects it."""
    return {
        "response_text": "Move valuables to upper shelves. Keep documents in waterproof bags.",
        "phase": "PREPARE",
        "confidence": 0.9,
        "action_items": ["Move valuables up", "Waterproof documents"],
        "warnings": [],
        "metadata": {"word_count": 11, "language": "English", "source": "live"},
    }


@pytest.fixture
def sample_reports() -> list[dict]:
    """Citizen reports in the shape Firestore returns them."""
    return [
        {
            "report_id": "r1",
            "pincode": "682001",
            "phone_hash": "a" * 64,
            "text": "Water at knee level near Aluva junction",
            "timestamp": "2026-07-11T06:00:00+00:00",
            "source": "whatsapp",
        },
        {
            "report_id": "r2",
            "pincode": "682001",
            "phone_hash": "b" * 64,
            "text": "Periyar river overflowing, families evacuating",
            "timestamp": "2026-07-11T06:30:00+00:00",
            "source": "whatsapp",
        },
    ]
