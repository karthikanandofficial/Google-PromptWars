from cachetools import TTLCache
from typing import Any

# Separate caches per TTL requirement
_prepare_cache: TTLCache = TTLCache(maxsize=512, ttl=1800)  # 30min for preparedness plans
_alert_cache: TTLCache = TTLCache(maxsize=512, ttl=300)     # 5min for live alerts

_CACHE_BY_PHASE = {
    "PREPARE": _prepare_cache,
    "ALERT": _alert_cache,
    "DURING": _alert_cache,
    "AFTER": _prepare_cache,
    "COORD": _alert_cache,
}


def _cache_for(phase: str) -> TTLCache:
    return _CACHE_BY_PHASE.get(phase.upper(), _prepare_cache)


def get_cached(pincode: str, phase: str, language: str) -> dict[str, Any] | None:
    key = (pincode, phase.upper(), language.lower())
    return _cache_for(phase).get(key)


def set_cached(pincode: str, phase: str, language: str, value: dict[str, Any]) -> None:
    key = (pincode, phase.upper(), language.lower())
    _cache_for(phase)[key] = value
