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
