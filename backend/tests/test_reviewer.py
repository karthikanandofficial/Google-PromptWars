from backend.agents.reviewer import validate_and_repair, _fallback_response


def test_valid_response_passes_through_unchanged(valid_gemini_response):
    result = validate_and_repair(valid_gemini_response, "PREPARE")

    assert result["response_text"] == valid_gemini_response["response_text"]
    assert result["confidence"] == 0.9
    assert result["warnings"] == []


def test_missing_fields_filled_with_defaults():
    result = validate_and_repair({"response_text": "some plan"}, "PREPARE")

    assert result["phase"] == "PREPARE"
    assert result["confidence"] == 0.5
    assert result["action_items"] == []
    assert isinstance(result["warnings"], list)
    assert "word_count" in result["metadata"]


def test_non_dict_input_returns_fallback():
    result = validate_and_repair("not a dict", "ALERT")  # type: ignore[arg-type]

    assert result["confidence"] == 0.0
    assert result["metadata"]["source"] == "fallback"
    assert "NDRF" in result["response_text"]


def test_low_confidence_appends_warning():
    response = {"response_text": "uncertain advice", "confidence": 0.3}

    result = validate_and_repair(response, "PREPARE")

    assert any("confidence" in w.lower() for w in result["warnings"])


def test_low_confidence_warning_not_duplicated():
    response = {
        "response_text": "text",
        "confidence": 0.2,
        "warnings": ["Low confidence response (0.20). Verify with local authorities."],
    }

    result = validate_and_repair(response, "PREPARE")

    confidence_warnings = [w for w in result["warnings"] if "confidence" in w.lower()]
    assert len(confidence_warnings) == 1


def test_empty_response_text_replaced_and_flagged():
    result = validate_and_repair({"response_text": "   "}, "ALERT")

    assert result["response_text"].strip() != ""
    assert result["confidence"] == 0.0
    assert any("empty" in w.lower() for w in result["warnings"])


def test_word_count_computed_when_metadata_missing():
    result = validate_and_repair({"response_text": "one two three four"}, "PREPARE")

    assert result["metadata"]["word_count"] == 4


def test_fallback_response_contains_emergency_numbers():
    result = _fallback_response("DURING", "test reason")

    assert "1070" in result["response_text"] or "NDRF" in result["response_text"]
    assert result["warnings"] == ["test reason"]
    assert len(result["action_items"]) > 0
