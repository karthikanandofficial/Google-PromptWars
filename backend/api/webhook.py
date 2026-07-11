import hashlib
import html
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Form, HTTPException, Request, Response
from twilio.request_validator import RequestValidator

from backend.agents.planner import route
from backend.config import settings
from backend.services.firestore import get_session, save_session

logger = logging.getLogger(__name__)

router = APIRouter()

_validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)


def _hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


def _sanitize_body(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.strip()[:500]
    return text


def _twiml(message: str) -> Response:
    safe = html.escape(message)
    body = f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>{safe}</Message></Response>"
    return Response(content=body, media_type="text/xml")


@router.post("/webhook")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(""),
    MediaUrl0: str | None = Form(None),
):
    # Validate Twilio signature before any processing
    form_data = dict(await request.form())
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")

    if not _validator.validate(url, form_data, signature):
        logger.warning(f"Invalid Twilio signature from {From[:4]}...")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    body = _sanitize_body(Body)
    if not body:
        return _twiml("Please send a text message.")

    phone_hash = _hash_phone(From)

    session = get_session(phone_hash) or {
        "phone_hash": phone_hash,
        "state": "ONBOARD",
        "language": "English",
        "pincode": "",
        "floor": "",
        "dependents": "",
        "transport": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response_text, updated_session = await route(session, body, phone_hash)
    except Exception as e:
        logger.error(f"Route error for {phone_hash[:8]}: {e}", exc_info=True)
        response_text = "Something went wrong. For emergencies call 1070 (State Emergency) or NDRF: 011-24363260."
        updated_session = session

    updated_session["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_session(phone_hash, updated_session)

    return _twiml(response_text)
