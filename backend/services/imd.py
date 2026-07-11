import json
import logging
import re
from pathlib import Path
from typing import TypedDict, Final

import httpx

logger = logging.getLogger(__name__)

IMD_RSS_URL: Final[str] = "https://mausam.imd.gov.in/imd_latest/contents/warning.php"
FALLBACK_PATH: Final[Path] = Path(__file__).parent.parent / "data" / "imd_fallback.json"

_fallback_data: dict | None = None


def _load_fallback() -> dict:
    global _fallback_data
    if _fallback_data is None:
        _fallback_data = json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))
    return _fallback_data


class RawAlert(TypedDict):
    headline: str
    detail: str
    alert_level: str
    district: str
    state: str
    source: str


async def fetch_imd_alert(pincode: str) -> RawAlert:
    """Fetch live IMD alert for a pincode. Falls back to bundled data on RSS failure."""
    prefix = pincode[:3]
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(IMD_RSS_URL)
            resp.raise_for_status()
            text = resp.text
            # Parse the page for relevant district warnings
            # IMD warning page is HTML with district-wise text
            alert_text = _extract_relevant_text(text, pincode)
            if alert_text:
                return RawAlert(
                    headline=f"IMD Live Warning for pincode {pincode}",
                    detail=alert_text,
                    alert_level="See detail",
                    district="",
                    state="",
                    source="live",
                )
    except Exception as e:
        logger.warning(f"IMD RSS fetch failed for pincode {pincode}: {e}; using fallback")

    return _get_fallback_alert(prefix)


def _extract_relevant_text(html: str, pincode: str) -> str:
    """Extract relevant warning text from IMD HTML page."""
    # Map prefixes to state names for keyword search
    prefix_to_state = {
        "682": "Kerala",
        "688": "Kerala",
        "689": "Kerala",
        "400": "Maharashtra",
        "781": "Assam",
        "751": "Odisha",
        "600": "Tamil Nadu",
        "560": "Karnataka",
        "700": "West Bengal",
    }
    prefix = pincode[:3]
    state = prefix_to_state.get(prefix)
    if not state:
        return ""

    # Simple extraction: find lines containing the state name
    lines = html.replace("<br>", "\n").replace("<BR>", "\n").split("\n")
    relevant = []
    for line in lines:
        stripped = line.strip()
        if state.lower() in stripped.lower() and len(stripped) > 20:
            clean = re.sub(r"<[^>]+>", "", stripped).strip()
            if clean:
                relevant.append(clean)
    return " ".join(relevant[:5]) if relevant else ""


def _get_fallback_alert(prefix: str) -> RawAlert:
    data = _load_fallback()
    for alert in data["alerts"]:
        if any(prefix.startswith(p) for p in alert["pincodes_prefix"]):
            return RawAlert(
                headline=alert["headline"],
                detail=alert["detail"],
                alert_level=alert["alert_level"],
                district=alert["district"],
                state=alert["state"],
                source="fallback",
            )
    # Generic fallback when no prefix match
    return RawAlert(
        headline="IMD General Monsoon Advisory",
        detail="Heavy rainfall expected in several districts. Stay alert, avoid flood-prone areas, keep emergency supplies ready. Check local authorities for specific advisories for your area.",
        alert_level="Yellow",
        district="",
        state="",
        source="fallback",
    )
