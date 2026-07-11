import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import TypedDict

from backend.agents.reviewer import validate_and_repair
from backend.prompts.templates import REPORT_ACK_TEMPLATE
from backend.services.firestore import CitizenReport, save_report
from backend.services.gemini import call_gemini

logger = logging.getLogger(__name__)


class ReportIntakeResult(TypedDict):
    report_id: str
    response_text: str
    saved: bool


async def intake_report(text: str, phone_hash: str, pincode: str, language: str) -> ReportIntakeResult:
    """Store a citizen report in Firestore and return an acknowledgement."""
    report_id = str(uuid.uuid4())

    report = CitizenReport(
        report_id=report_id,
        pincode=pincode,
        phone_hash=phone_hash,
        text=text[:500],  # cap length at storage
        timestamp=datetime.now(timezone.utc).isoformat(),
        source="whatsapp",
    )

    try:
        save_report(report)
        saved = True
    except Exception as e:
        logger.error(f"Failed to save report {report_id}: {e}")
        saved = False

    system = REPORT_ACK_TEMPLATE.format(language=language, report_id=report_id[:8])
    raw = await call_gemini(system, f"Report text: {text[:100]}")
    validated = validate_and_repair(raw, "REPORT")

    return ReportIntakeResult(
        report_id=report_id,
        response_text=validated["response_text"],
        saved=saved,
    )
