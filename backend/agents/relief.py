import json
import logging
from pathlib import Path
from typing import Final, TypedDict

from backend.agents.reviewer import validate_and_repair
from backend.prompts.templates import SYSTEM_TEMPLATE
from backend.services.gemini import call_gemini

logger = logging.getLogger(__name__)

SCHEMES_PATH: Final[Path] = Path(__file__).parent.parent / "data" / "schemes.json"

_schemes_text: str | None = None


def _load_schemes() -> str:
    global _schemes_text
    if _schemes_text is None:
        data = json.loads(SCHEMES_PATH.read_text(encoding="utf-8"))
        lines = []
        for s in data["schemes"]:
            docs = ", ".join(s["required_documents"])
            lines.append(
                f"SCHEME: {s['name']} ({s['id']})\n"
                f"Eligibility: {s['eligibility']}\n"
                f"Documents: {docs}\n"
                f"Apply: {s['application_process']}\n"
                f"Contact: {s['contact']}\n"
            )
        _schemes_text = "\n---\n".join(lines)
    return _schemes_text


class SchemeMatch(TypedDict):
    response_text: str
    phase: str
    confidence: float
    action_items: list[str]
    warnings: list[str]
    metadata: dict


async def match_schemes(loss_description: str, language: str, pincode: str = "000000") -> SchemeMatch:
    """Match government relief schemes to described losses. Injects full schemes.json as context."""
    scheme_rules = _load_schemes()

    system = SYSTEM_TEMPLATE.format(
        phase="AFTER",
        risk_tier="MEDIUM",
        pincode=pincode,
        language=language,
        floor="unknown",
        dependents="unknown",
        transport="unknown",
        max_words=300,
        scheme_rules=scheme_rules,
        aggregated_reports="",
    )

    user_msg = (
        f"A citizen has described the following loss/damage:\n\n{loss_description}\n\n"
        f"Match the applicable government relief schemes and provide: scheme name, why they're eligible, "
        f"required documents, and a draft application paragraph in {language}."
    )

    raw = await call_gemini(system, user_msg)
    return validate_and_repair(raw, "AFTER")
