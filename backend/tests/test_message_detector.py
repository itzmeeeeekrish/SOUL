"""Tests for the local, provisional message detector."""

import pytest

from app.services.message_detector import analyze_message


class FakePipeline:
    classes_ = ["legitimate", "scam", "spam"]

    def predict(self, texts):
        assert len(texts) == 1
        return ["scam"]

    def predict_proba(self, texts):
        assert len(texts) == 1
        return [[0.10, 0.80, 0.10]]


def test_analyze_message_returns_provisional_label_and_safe_guidance():
    result = analyze_message(
        "Your account will be blocked. Share your OTP.",
        FakePipeline(),
    )

    assert result["analysis_status"] == "provisional_model_suggestion"
    assert result["candidate_label"] == "scam"
    assert result["model_scores"] == {
        "legitimate": 0.10,
        "scam": 0.80,
        "spam": 0.10,
    }
    assert result["top_model_score"] == pytest.approx(0.80)
    assert result["low_score_separation"] is False
    assert result["review_required"] is True
    assert "Do not share OTPs" in result["guidance"]
    assert any("uncalibrated" in item for item in result["limitations"])


def test_analyze_message_rejects_blank_text():
    with pytest.raises(ValueError, match="must not be blank"):
        analyze_message("   ", FakePipeline())


def test_analyze_message_rejects_text_over_limit():
    with pytest.raises(ValueError, match="at most 5000"):
        analyze_message("x" * 5001, FakePipeline())


def test_analyze_message_flags_close_model_scores():
    class ClosePipeline(FakePipeline):
        def predict_proba(self, texts):
            return [[0.34, 0.35, 0.31]]

        def predict(self, texts):
            return ["scam"]

    result = analyze_message("Some message", ClosePipeline())

    assert result["low_score_separation"] is True
    assert result["review_required"] is True


def test_analyze_message_rejects_unexpected_model_labels():
    class InvalidPipeline(FakePipeline):
        classes_ = ["legitimate", "fraud", "spam"]

    with pytest.raises(RuntimeError, match="unexpected label schema"):
        analyze_message("Some message", InvalidPipeline())


def test_analyze_message_abstains_for_devanagari_before_model_call():
    class MustNotRun:
        classes_ = ["legitimate", "scam", "spam"]

        def predict(self, _texts):
            raise AssertionError("The baseline must not classify Devanagari text.")

        def predict_proba(self, _texts):
            raise AssertionError("The baseline must not score Devanagari text.")

    result = analyze_message("आपका बैंक खाता आज बंद हो जाएगा।", MustNotRun())

    assert result["analysis_status"] == "abstained_unsupported_language"
    assert result["candidate_label"] == "needs_review"
    assert result["model_scores"] == {}
    assert result["review_required"] is True
    assert result["language_assessment"]["script_profile"] == "non_latin"


def test_analyze_message_abstains_for_romanized_hinglish_before_model_call():
    class MustNotRun:
        classes_ = ["legitimate", "scam", "spam"]

        def predict(self, _texts):
            raise AssertionError("The baseline must not classify Romanized Hinglish.")

        def predict_proba(self, _texts):
            raise AssertionError("The baseline must not score Romanized Hinglish.")

    result = analyze_message("Aapka bank khata band hai. OTP bheje.", MustNotRun())

    assert result["analysis_status"] == "abstained_unsupported_language"
    assert result["candidate_label"] == "needs_review"
    assert result["review_required"] is True
    assert result["language_assessment"]["baseline_eligible"] is False


def test_analyze_message_returns_language_assessment_for_latin_text():
    result = analyze_message("Your delivery is scheduled for tomorrow.", FakePipeline())

    assert result["analysis_status"] == "provisional_model_suggestion"
    assert result["language_assessment"]["script_profile"] == "latin"
    assert result["language_assessment"]["baseline_eligible"] is True



def test_analysis_includes_text_indicators_and_source_backed_guidance():
    result = analyze_message(
        "URGENT: Update KYC now at https://example.invalid and share your OTP.",
        FakePipeline(),
    )

    codes = {item["code"] for item in result["risk_indicators"]}
    guidance_ids = {item["id"] for item in result["official_guidance"]}

    assert {"credential_request", "urgency_or_threat",
            "kyc_or_account_update", "url_present"} <= codes
    assert "rbi_kyc_fraud_2026" in guidance_ids
    assert "dot_chakshu" in guidance_ids
    assert "curated keyword rules" in result["guidance_retrieval_note"]
    assert result["candidate_label"] == "scam"
    assert result["review_required"] is True


def test_indicator_rules_do_not_override_model_prediction():
    class LegitimatePipeline(FakePipeline):
        def predict(self, texts):
            return ["legitimate"]

        def predict_proba(self, texts):
            return [[0.80, 0.10, 0.10]]

    result = analyze_message(
        "Share your OTP immediately.",
        LegitimatePipeline(),
    )

    assert result["candidate_label"] == "legitimate"
    assert any(
        item["code"] == "credential_request"
        for item in result["risk_indicators"]
    )
    assert result["review_required"] is True


def test_unsupported_script_still_returns_keyword_indicators_and_guidance():
    result = analyze_message(
        "कृपया share your OTP now.",
        FakePipeline(),
    )

    assert result["analysis_status"] == "abstained_unsupported_language"
    assert result["candidate_label"] == "needs_review"
    assert any(
        item["code"] == "credential_request"
        for item in result["risk_indicators"]
    )
    assert result["official_guidance"]
