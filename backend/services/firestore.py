import base64
import json
import logging
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import TypedDict

import firebase_admin
from firebase_admin import credentials, firestore

from backend.config import settings

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).parent.parent

_app: firebase_admin.App | None = None
_db = None


def _resolve_cred_path(raw: str) -> str:
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    return str(_BACKEND_DIR / p)


def _build_credentials() -> credentials.Certificate:
    """Build Firebase credentials from env var JSON (base64) or file path."""
    if settings.FIREBASE_CREDENTIALS_JSON:
        # Render deployment: credentials passed as base64-encoded JSON env var
        raw_json = base64.b64decode(settings.FIREBASE_CREDENTIALS_JSON).decode("utf-8")
        cred_dict = json.loads(raw_json)
        return credentials.Certificate(cred_dict)
    if settings.FIREBASE_CREDENTIALS_PATH:
        cred_path = _resolve_cred_path(settings.FIREBASE_CREDENTIALS_PATH)
        return credentials.Certificate(cred_path)
    raise RuntimeError("Neither FIREBASE_CREDENTIALS_JSON nor FIREBASE_CREDENTIALS_PATH is set")


def _get_db():
    global _app, _db
    if _db is None:
        if not firebase_admin._apps:
            cred = _build_credentials()
            _app = firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db


class UserSession(TypedDict):
    phone_hash: str
    state: str
    language: str
    pincode: str
    floor: str
    dependents: str
    transport: str
    created_at: str
    updated_at: str


class CitizenReport(TypedDict):
    report_id: str
    pincode: str
    phone_hash: str
    text: str
    timestamp: str
    source: str


def save_session(phone_hash: str, session: UserSession) -> None:
    db = _get_db()
    db.collection("sessions").document(phone_hash).set(session, merge=True)
    logger.debug(f"Session saved for {phone_hash[:8]}...")


def get_session(phone_hash: str) -> UserSession | None:
    db = _get_db()
    doc = db.collection("sessions").document(phone_hash).get()
    if doc.exists:
        return doc.to_dict()
    return None


def save_report(report: CitizenReport) -> None:
    db = _get_db()
    db.collection("reports").document(report["report_id"]).set(report)
    logger.info(f"Report {report['report_id']} saved for pincode {report['pincode']}")


def get_reports(pincode: str, hours: int = 6) -> list[CitizenReport]:
    db = _get_db()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_str = since.isoformat()

    try:
        docs = (
            db.collection("reports")
            .where(filter=firestore.FieldFilter("pincode", "==", pincode))
            .where(filter=firestore.FieldFilter("timestamp", ">=", since_str))
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(50)
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        if "requires an index" in str(e):
            # Index still building — fall back to pincode-only query (no time filter)
            logger.warning(f"Composite index not ready, falling back to pincode-only query: {e}")
            docs = (
                db.collection("reports")
                .where(filter=firestore.FieldFilter("pincode", "==", pincode))
                .limit(20)
                .stream()
            )
            return [doc.to_dict() for doc in docs]
        raise


def ping_firestore() -> bool:
    """Health check — returns True if Firestore is reachable."""
    try:
        db = _get_db()
        db.collection("_health").document("ping").get()
        return True
    except Exception as e:
        logger.error(f"Firestore health check failed: {e}")
        return False
