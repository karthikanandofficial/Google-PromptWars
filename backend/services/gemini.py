import json
import logging
from typing import Any

from google import genai
from google.genai import types

from backend.config import settings

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.GEMINI_API_KEY)

_GENERATION_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json",
    temperature=0.2,
)


async def call_gemini(system: str, user: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call Gemini with structured JSON output. Retries up to 3x on parse failure."""
    full_prompt = f"{system}\n\nUser input: {user}"
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            response = _client.models.generate_content(
                model="gemini-3.5-flash",
                contents=full_prompt,
                config=_GENERATION_CONFIG,
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"Gemini JSON parse failure (attempt {attempt + 1}/3): {e}")
        except Exception as e:
            last_error = e
            logger.error(f"Gemini API error (attempt {attempt + 1}/3): {e}")
            raise

    logger.error(f"Gemini failed after 3 attempts: {last_error}")
    raise ValueError(f"Gemini returned unparseable JSON after 3 attempts: {last_error}") from last_error
