import asyncio
import logging
import re

from backend.agents.alert import get_alert
from backend.agents.coordinator import synthesize_triage
from backend.agents.prepare import HouseholdProfile, generate_plan
from backend.agents.relief import match_schemes
from backend.agents.report import intake_report
from backend.agents.vulnerability import get_risk_tier
from backend.services.gemini import call_gemini
from backend.prompts.templates import ONBOARD_TEMPLATE, PINCODE_TEMPLATE, PROFILE_COLLECT_TEMPLATE
from backend.agents.reviewer import validate_and_repair

logger = logging.getLogger(__name__)

KEYWORD_PATTERNS = {
    "PREPARE": re.compile(r"\b(prepare|preparat|ready|plan|before|checklist|तैयार|तैयारी)\b", re.IGNORECASE),
    "ALERT": re.compile(r"\b(alert|warning|forecast|imd|weather|rain|flood|danger|खतरा|चेतावनी)\b", re.IGNORECASE),
    "REPORT": re.compile(r"\b(report|water|flood|knee|waist|road|block|stuck|stranded|help|rescue|पानी|बाढ़)\b", re.IGNORECASE),
    "RELIEF": re.compile(r"\b(relief|scheme|claim|compensation|damage|loss|money|नुकसान|सहायता|मुआवजा)\b", re.IGNORECASE),
    "COORD": re.compile(r"\b(coord|triage|brief|summary|coordinator|dashboard|ward)\b", re.IGNORECASE),
}

PROFILE_FIELDS = ["floor", "dependents", "transport"]


def detect_intent(text: str) -> str | None:
    for intent, pattern in KEYWORD_PATTERNS.items():
        if pattern.search(text):
            return intent
    return None


def _missing_profile_fields(session: dict) -> list[str]:
    return [f for f in PROFILE_FIELDS if not session.get(f)]


async def route(session: dict, body: str, phone_hash: str) -> tuple[str, dict]:
    """
    Route incoming message to the correct agent.
    Returns (response_text, updated_session).
    """
    state = session.get("state", "ONBOARD")
    body_clean = body.strip()

    # ── ONBOARDING ──────────────────────────────────────────────────────────
    if state == "ONBOARD":
        raw = await call_gemini(ONBOARD_TEMPLATE, body_clean)
        validated = validate_and_repair(raw, "ONBOARD")
        session["state"] = "AWAIT_LANGUAGE"
        return validated["response_text"], session

    if state == "AWAIT_LANGUAGE":
        lang = _parse_language(body_clean)
        session["language"] = lang
        session["state"] = "AWAIT_PINCODE"
        raw = await call_gemini(PINCODE_TEMPLATE.format(language=lang), body_clean)
        validated = validate_and_repair(raw, "AWAIT_PINCODE")
        return validated["response_text"], session

    if state == "AWAIT_PINCODE":
        pincode = _parse_pincode(body_clean)
        if not pincode:
            return "Please send your 6-digit pincode (e.g. 682001).", session
        session["pincode"] = pincode
        session["state"] = "READY"
        risk = get_risk_tier(pincode)
        lang = session.get("language", "en")
        tip = _risk_greeting(risk["tier"].value, lang)
        return tip, session

    # ── COLLECT PROFILE ─────────────────────────────────────────────────────
    if state == "COLLECT_PROFILE":
        collecting = session.get("collecting_field")
        if collecting:
            session[collecting] = body_clean[:50]
        missing = _missing_profile_fields(session)
        if missing:
            lang = session.get("language", "en")
            raw = await call_gemini(
                PROFILE_COLLECT_TEMPLATE.format(language=lang, missing_fields=", ".join(missing)),
                body_clean,
            )
            validated = validate_and_repair(raw, "COLLECT_PROFILE")
            session["collecting_field"] = validated.get("asking_field", missing[0])
            return validated["response_text"], session
        # Profile complete → run plan
        session["state"] = "READY"
        return await _run_prepare(session, phone_hash)

    # ── READY — detect intent ────────────────────────────────────────────────
    intent = detect_intent(body_clean)

    if not intent:
        # Free text: continue last active flow or give help
        last = session.get("last_intent")
        if last == "PREPARE":
            return await _run_prepare(session, phone_hash)
        return (
            "Send one of: PREPARE (get a plan), ALERT (weather warning), "
            "REPORT (log a situation), RELIEF (scheme info).",
            session,
        )

    session["last_intent"] = intent

    if intent == "PREPARE":
        missing = _missing_profile_fields(session)
        if missing:
            session["state"] = "COLLECT_PROFILE"
            session["collecting_field"] = None
            lang = session.get("language", "en")
            raw = await call_gemini(
                PROFILE_COLLECT_TEMPLATE.format(language=lang, missing_fields=", ".join(missing)),
                body_clean,
            )
            validated = validate_and_repair(raw, "COLLECT_PROFILE")
            session["collecting_field"] = validated.get("asking_field", missing[0])
            return validated["response_text"], session
        return await _run_prepare(session, phone_hash)

    if intent == "ALERT":
        pincode = session.get("pincode", "000000")
        lang = session.get("language", "en")
        result = await get_alert(pincode, lang)
        return result["response_text"], session

    if intent == "REPORT":
        pincode = session.get("pincode", "000000")
        lang = session.get("language", "en")
        result = await intake_report(body_clean, phone_hash, pincode, lang)
        return result["response_text"], session

    if intent == "RELIEF":
        lang = session.get("language", "en")
        pincode = session.get("pincode", "000000")
        result = await match_schemes(body_clean, lang, pincode)
        return result["response_text"], session

    if intent == "COORD":
        pincode = session.get("pincode", "000000")
        result = await synthesize_triage(pincode)
        return result["response_text"], session

    return "How can I help you? Send PREPARE, ALERT, REPORT, or RELIEF.", session


async def _run_prepare(session: dict, phone_hash: str) -> tuple[str, dict]:
    pincode = session.get("pincode", "000000")
    lang = session.get("language", "en")

    # Run vulnerability lookup and any prep concurrently
    risk = get_risk_tier(pincode)

    profile = HouseholdProfile(
        pincode=pincode,
        floor=session.get("floor", "ground floor"),
        dependents=session.get("dependents", "none"),
        transport=session.get("transport", "unknown"),
        language=lang,
        hours_until_event=48,
    )
    result = await generate_plan(profile, risk)
    return result["response_text"], session


def _parse_language(text: str) -> str:
    text_lower = text.lower().strip()
    lang_map = {
        "english": "English", "1": "English",
        "hindi": "Hindi", "हिंदी": "Hindi", "2": "Hindi",
        "tamil": "Tamil", "தமிழ்": "Tamil", "3": "Tamil",
        "telugu": "Telugu", "తెలుగు": "Telugu", "4": "Telugu",
        "kannada": "Kannada", "ಕನ್ನಡ": "Kannada", "5": "Kannada",
        "malayalam": "Malayalam", "മലയാളം": "Malayalam", "6": "Malayalam",
    }
    return lang_map.get(text_lower, "English")


def _parse_pincode(text: str) -> str | None:
    match = re.search(r"\b(\d{6})\b", text)
    return match.group(1) if match else None


def _risk_greeting(tier: str, lang: str) -> str:
    greetings = {
        "HIGH": "Your area has HIGH flood risk. I'll help you prepare, get alerts, and file relief claims. Send PREPARE to start.",
        "MEDIUM": "Your area has MEDIUM flood risk. Send PREPARE for a plan, ALERT for weather updates, or RELIEF for scheme info.",
        "LOW": "Your area has LOW flood risk this season. Send PREPARE for precautions or ALERT for the latest IMD update.",
    }
    return greetings.get(tier, greetings["MEDIUM"])
