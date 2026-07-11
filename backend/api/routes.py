import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from backend.agents.coordinator import synthesize_triage
from backend.agents.relief import match_schemes
from backend.services.firestore import get_reports, ping_firestore
from backend.services.gemini import call_gemini

logger = logging.getLogger(__name__)

router = APIRouter()

PINCODE_RE = re.compile(r"^\d{6}$")


class TriageRequest(BaseModel):
    pincode: str
    hours: int = 6

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        if not PINCODE_RE.match(v):
            raise ValueError("pincode must be exactly 6 numeric digits")
        return v


class ReliefRequest(BaseModel):
    description: str
    language: str = "English"

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description must not be empty")
        return v[:1000]


async def _sse_stream(generator: AsyncGenerator[dict[str, Any], None]) -> AsyncGenerator[str, None]:
    """Wrap a dict generator into SSE wire format, terminated by [DONE]."""
    async for chunk in generator:
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


async def _triage_generator(pincode: str, hours: int) -> AsyncGenerator[dict[str, Any], None]:
    """Stream triage progress stages, then the final coordinator brief."""
    yield {"stage": "Fetching reports...", "done": False}
    await asyncio.sleep(0)  # yield control so the first stage flushes before the Gemini call

    yield {"stage": "Analyzing...", "done": False}
    result = await synthesize_triage(pincode, hours)

    yield {"stage": "Generating brief...", "done": False}
    yield {"stage": "Complete", "done": True, "result": result}


async def _relief_generator(description: str, language: str) -> AsyncGenerator[dict[str, Any], None]:
    """Stream relief-matching progress stages, then the matched schemes."""
    yield {"stage": "Reading your description...", "done": False}
    await asyncio.sleep(0)

    yield {"stage": "Matching schemes...", "done": False}
    result = await match_schemes(description, language)

    yield {"stage": "Complete", "done": True, "result": result}


@router.post("/api/triage")
async def triage(req: TriageRequest):
    return StreamingResponse(
        _sse_stream(_triage_generator(req.pincode, req.hours)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/relief")
async def relief(req: ReliefRequest):
    return StreamingResponse(
        _sse_stream(_relief_generator(req.description, req.language)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/reports/{pincode}")
async def reports(pincode: str, hours: int = 6):
    if not PINCODE_RE.match(pincode):
        raise HTTPException(status_code=422, detail="pincode must be 6 numeric digits")
    return {"reports": get_reports(pincode, hours)}


@router.get("/api/alert")
async def alert_endpoint(pincode: str = "682001", language: str = "English"):
    from backend.agents.alert import get_alert
    if not PINCODE_RE.match(pincode):
        raise HTTPException(status_code=422, detail="pincode must be 6 numeric digits")
    return await get_alert(pincode, language)


@router.get("/api/health")
async def health():
    gemini_ok = False
    firestore_ok = False

    try:
        result = await call_gemini(
            "Reply with exactly: {\"status\": \"ok\"}",
            "health check",
        )
        gemini_ok = result.get("status") == "ok"
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")

    try:
        firestore_ok = ping_firestore()
    except Exception as e:
        logger.error(f"Firestore health check failed: {e}")

    return {
        "gemini": "ok" if gemini_ok else "error",
        "firestore": "ok" if firestore_ok else "error",
    }
