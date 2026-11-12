"""Tests for the conservative language/script coverage guard."""

from app.services.language_guard import inspect_language_support


def test_ordinary_latin_text_is_eligible_but_not_claimed_as_english():
    result = inspect_language_support(
        "Your delivery is scheduled for tomorrow."
    )

    assert result["script_profile"] == "latin"
    assert result["baseline_eligible"] is True
    assert result["coverage_status"] == "unvalidated_latin_text"
    assert "does not prove" in result["coverage_note"]


def test_devanagari_hindi_is_not_sent_to_the_english_first_baseline():
    result = inspect_language_support(
        "आपका बैंक खाता आज बंद हो जाएगा।"
    )

    assert result["script_profile"] == "non_latin"
    assert result["baseline_eligible"] is False
    assert result["coverage_status"] == "unvalidated_non_english_or_mixed_language"


def test_romanized_hinglish_is_flagged_by_distinctive_markers():
    result = inspect_language_support(
        "Aapka bank khata band ho jayega. OTP bheje."
    )

    assert result["script_profile"] == "latin"
    assert result["romanized_hindi_markers"]
    assert result["baseline_eligible"] is False


def test_mixed_devanagari_and_latin_text_is_not_eligible():
    result = inspect_language_support(
        "Your account बंद हो जाएगा"
    )

    assert result["script_profile"] == "mixed_latin_non_latin"
    assert result["baseline_eligible"] is False


def test_marker_detection_is_case_insensitive():
    result = inspect_language_support("AAPKA account band hai")

    assert result["baseline_eligible"] is False
    assert set(result["romanized_hindi_markers"]) == {"aapka", "band", "hai"}


def test_common_english_words_do_not_trigger_hinglish_signal():
    result = inspect_language_support(
        "Please contact your bank for account information."
    )

    assert result["romanized_hindi_markers"] == []
    assert result["baseline_eligible"] is True
