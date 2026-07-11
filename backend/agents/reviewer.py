import logging
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = {"response_text", "phase", "confidence", "action_items", "warnings", "metadata"}
REQUIRED_METADATA = {"word_count", "language", "source"}


def validate_and_repair(response: dict[str, Any], phase: str) -> dict[str, Any]:
    """Validate Gemini output schema. Fills missing fields rather than crashing."""
    if not isinstance(response, dict):
        logger.error(f"Reviewer received non-dict response: {type(response)}")
        return _fallback_response(phase, "Response was not a valid JSON object.")

    repaired = dict(response)

    # Fill missing top-level fields
    repaired.setdefault("response_text", "")
    repaired.setdefault("phase", phase)
    repaired.setdefault("confidence", 0.5)
    repaired.setdefault("action_items", [])
    repaired.setdefault("warnings", [])
    repaired.setdefault("metadata", {})

    # Fill missing metadata fields
    meta = repaired["metadata"]
    meta.setdefault("word_count", len(repaired["response_text"].split()))
    meta.setdefault("language", "en")
    meta.setdefault("source", "live")

    # Low-confidence warning
    if repaired["confidence"] < 0.5:
        if not any("confidence" in w.lower() for w in repaired["warnings"]):
            repaired["warnings"].append(
                f"Low confidence response ({repaired['confidence']:.2f}). Verify with local authorities."
            )

    # Empty response warning
    if not repaired["response_text"].strip():
        logger.warning("Reviewer: empty response_text received from Gemini")
        repaired["response_text"] = "Unable to generate a response at this time. Please try again or contact local authorities."
        repaired["confidence"] = 0.0
        repaired["warnings"].append("Empty response from AI model.")

    return repaired


def _fallback_response(phase: str, reason: str) -> dict[str, Any]:
    return {
        "response_text": "Service temporarily unavailable. For emergencies, call NDRF: 011-24363260 or State Emergency: 1070.",
        "phase": phase,
        "confidence": 0.0,
        "action_items": ["Call NDRF helpline: 011-24363260", "Call State Emergency Operations Centre: 1070"],
        "warnings": [reason],
        "metadata": {"word_count": 15, "language": "en", "source": "fallback"},
    }
