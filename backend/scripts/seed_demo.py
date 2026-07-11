"""
One-time seed script. Run: python -m backend.scripts.seed_demo
Writes 5 realistic citizen reports to Firestore across Ernakulam and Mumbai.
Not part of app startup.
"""
import hashlib
import uuid
from datetime import datetime, timezone, timedelta

from backend.services.firestore import CitizenReport, save_report


def _fake_phone_hash(n: int) -> str:
    return hashlib.sha256(f"demo_citizen_{n}".encode()).hexdigest()


DEMO_REPORTS = [
    {
        "pincode": "682001",
        "text": "Water level at knee height near Kaloor junction. Road completely blocked. Several cars stranded.",
        "hours_ago": 1,
    },
    {
        "pincode": "682001",
        "text": "Power outage since 3 AM in Edappally. Transformer submerged. Please send help.",
        "hours_ago": 2,
    },
    {
        "pincode": "682001",
        "text": "Ground floor of building at MG Road flooded. 4 elderly residents need evacuation assistance.",
        "hours_ago": 3,
    },
    {
        "pincode": "400001",
        "text": "Underpass near CST fully waterlogged, waist deep. Traffic diverted. Avoid Byculla.",
        "hours_ago": 1,
    },
    {
        "pincode": "400001",
        "text": "Dharavi area low-lying roads flooded. Community kitchen has set up relief in school.",
        "hours_ago": 4,
    },
]


def seed():
    now = datetime.now(timezone.utc)
    for i, r in enumerate(DEMO_REPORTS):
        ts = (now - timedelta(hours=r["hours_ago"])).isoformat()
        report = CitizenReport(
            report_id=str(uuid.uuid4()),
            pincode=r["pincode"],
            phone_hash=_fake_phone_hash(i),
            text=r["text"],
            timestamp=ts,
            source="demo_seed",
        )
        save_report(report)
        print(f"Seeded report {i+1}: {r['pincode']} — {r['text'][:50]}...")
    print("Seed complete.")


if __name__ == "__main__":
    seed()
