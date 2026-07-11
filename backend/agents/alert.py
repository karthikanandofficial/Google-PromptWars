import logging

from backend.agents.reviewer import validate_and_repair
from backend.agents.vulnerability import get_risk_tier
from backend.cache.response_cache import get_cached, set_cached
from backend.prompts.templates import ALERT_TRANSLATE_TEMPLATE
from backend.services.gemini import call_gemini
from backend.services.imd import fetch_imd_alert

logger = logging.getLogger(__name__)


async def get_alert(pincode: str, language: str) -> dict:
    """Fetch and translate IMD alert for a pincode. 300s cache."""
    cached = get_cached(pincode, "ALERT", language)
    if cached:
        logger.debug(f"Cache hit: ALERT for {pincode}/{language}")
        return cached

    risk = get_risk_tier(pincode)
    raw_alert = await fetch_imd_alert(pincode)

    system = ALERT_TRANSLATE_TEMPLATE.format(
        language=language,
        pincode=pincode,
        risk_tier=risk["tier"].value,
        raw_alert=raw_alert["detail"],
        source=raw_alert["source"],
    )

    user_msg = f"Alert for pincode {pincode}, risk tier {risk['tier'].value}. Headline: {raw_alert['headline']}"

    raw = await call_gemini(system, user_msg)
    result = validate_and_repair(raw, "ALERT")
    # Preserve original source from IMD fetch
    result["metadata"]["source"] = raw_alert["source"]
    set_cached(pincode, "ALERT", language, result)
    return result
