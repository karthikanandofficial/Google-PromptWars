from backend.cache.response_cache import get_cached, set_cached


def test_set_then_get_returns_value():
    payload = {"response_text": "cached plan"}

    set_cached("682001", "PREPARE", "Malayalam", payload)
    result = get_cached("682001", "PREPARE", "Malayalam")

    assert result == payload


def test_miss_returns_none():
    assert get_cached("111111", "PREPARE", "English") is None


def test_key_is_case_insensitive_for_phase_and_language():
    payload = {"response_text": "case test"}

    set_cached("560001", "alert", "ENGLISH", payload)
    result = get_cached("560001", "ALERT", "english")

    assert result == payload


def test_different_language_is_a_different_key():
    set_cached("400001", "PREPARE", "Hindi", {"response_text": "hindi plan"})

    assert get_cached("400001", "PREPARE", "Tamil") is None


def test_different_pincode_is_a_different_key():
    set_cached("400001", "ALERT", "English", {"response_text": "mumbai alert"})

    assert get_cached("400002", "ALERT", "English") is None


def test_unknown_phase_falls_back_to_prepare_cache():
    # Unknown phase must not raise — routes to the default cache
    set_cached("682001", "UNKNOWN_PHASE", "English", {"response_text": "x"})

    assert get_cached("682001", "UNKNOWN_PHASE", "English") == {"response_text": "x"}
