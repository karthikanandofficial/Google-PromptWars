import logging
from typing import TypedDict

from backend.agents.reviewer import validate_and_repair
from backend.agents.vulnerability import RiskTier, RiskResult
from backend.cache.response_cache import get_cached, set_cached
from backend.prompts.templates import SYSTEM_TEMPLATE
from backend.services.gemini import call_gemini

logger = logging.getLogger(__name__)

PHASE_MAX_WORDS = {
    ("HIGH", "PREPARE"): 200,
    ("MEDIUM", "PREPARE"): 150,
    ("LOW", "PREPARE"): 120,
}


class HouseholdProfile(TypedDict):
    pincode: str
    floor: str
    dependents: str
    transport: str
    language: str
    hours_until_event: int


async def generate_plan(profile: HouseholdProfile, risk: RiskResult) -> dict:
    """Generate a phase-aware preparedness plan. Checks cache before calling Gemini."""
    pincode = profile["pincode"]
    language = profile["language"]
    phase = "PREPARE"

    cached = get_cached(pincode, phase, language)
    if cached:
        logger.debug(f"Cache hit: PREPARE plan for {pincode}/{language}")
        return cached

    tier_key = (risk["tier"].value, phase)
    max_words = PHASE_MAX_WORDS.get(tier_key, 150)

    system = SYSTEM_TEMPLATE.format(
        phase=phase,
        risk_tier=risk["tier"].value,
        pincode=pincode,
        language=language,
        floor=profile["floor"],
        dependents=profile["dependents"],
        transport=profile["transport"],
        max_words=max_words,
        scheme_rules="",
        aggregated_reports="",
    )

    user_msg = (
        f"Generate a monsoon preparedness plan. "
        f"Hours until possible event: {profile['hours_until_event']}. "
        f"District: {risk['district']}, {risk['state']}. "
        f"Flood frequency: {risk['flood_frequency']} times in last decade."
    )

    raw = await call_gemini(system, user_msg)
    result = validate_and_repair(raw, phase)
    set_cached(pincode, phase, language, result)
    return result
