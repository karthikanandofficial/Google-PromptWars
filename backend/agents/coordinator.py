import logging

from backend.agents.reviewer import validate_and_repair
from backend.prompts.templates import SYSTEM_TEMPLATE
from backend.services.firestore import get_reports
from backend.services.gemini import call_gemini

logger = logging.getLogger(__name__)


async def synthesize_triage(pincode: str, hours: int = 6) -> dict:
    """Aggregate citizen reports and produce a priority-ranked coordinator brief."""
    reports = get_reports(pincode, hours)

    if not reports:
        return {
            "response_text": f"No citizen reports found for pincode {pincode} in the last {hours} hours.",
            "phase": "COORD",
            "confidence": 1.0,
            "action_items": ["No reports to triage. Monitor incoming citizen messages."],
            "warnings": [],
            "metadata": {"word_count": 15, "language": "en", "source": "live"},
        }

    aggregated = "\n".join(
        f"[{r.get('timestamp', '?')}] Pincode {r.get('pincode', '?')}: {r.get('text', '')}"
        for r in reports
    )

    system = SYSTEM_TEMPLATE.format(
        phase="COORD",
        risk_tier="HIGH",
        pincode=pincode,
        language="English",
        floor="n/a",
        dependents="n/a",
        transport="n/a",
        max_words=150,
        scheme_rules="",
        aggregated_reports=aggregated,
    )

    user_msg = (
        f"You have {len(reports)} citizen reports from pincode {pincode} in the last {hours} hours. "
        f"Synthesize into a coordinator triage brief with CRITICAL/HIGH/MEDIUM priority actions."
    )

    raw = await call_gemini(system, user_msg)
    return validate_and_repair(raw, "COORD")
