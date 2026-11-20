import sys
from pathlib import Path

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_baseline_error_features import build_feature_error_report


def make_pipeline():
    train_texts = [
        "normal bank statement ready",
        "account statement available",
        "hello friend see you tomorrow",
        "bank account security notice",
        "verify bank account password immediately",
        "share your otp now",
        "urgent account verification required",
        "win a free prize today",
        "special discount offer buy now",
        "cheap holiday sale today",
    ]
    train_labels = [
        "legitimate",
        "legitimate",
        "legitimate",
        "legitimate",
        "scam",
        "scam",
        "scam",
        "spam",
        "spam",
        "spam",
    ]
    pipeline = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    pipeline.fit(train_texts, train_labels)
    return pipeline


def test_feature_report_is_validation_only_and_does_not_export_messages():
    secret_text = "opaque-private-message-zebra-9917"
    rows = [
        {"text": "win a free prize today", "label": "spam"},
        {"text": "verify bank account password immediately", "label": "spam"},
        {"text": secret_text, "label": "legitimate"},
    ]

    report = build_feature_error_report(rows, make_pipeline())
    serialised = str(report)

    assert report["split"] == "validation_only"
    assert report["total_rows"] == 3
    assert report["misclassified_rows"] >= 1
    assert secret_text not in serialised
    assert "message_text_exported" in report["privacy"]
    assert report["privacy"]["message_text_exported"] is False
    assert report["scope"]["test_split_read"] is False
    assert report["scope"]["model_retrained"] is False
    assert report["scope"]["thresholds_or_parameters_tuned"] is False


def test_feature_report_groups_errors_and_includes_contrastive_features():
    rows = [
        {"text": "verify bank account password immediately", "label": "spam"},
        {"text": "share your otp now", "label": "legitimate"},
    ]

    report = build_feature_error_report(rows, make_pipeline())

    assert report["misclassified_rows"] >= 1
    assert report["error_pairs"]
    for pair in report["error_pairs"]:
        assert pair["count"] >= 1
        assert pair["mean_vocabulary_coverage"] is not None
        assert "top_contrastive_features" in pair
        for feature in pair["top_contrastive_features"]:
            assert feature["error_count"] >= 1
            assert feature["mean_positive_logit_contribution"] > 0


def test_feature_report_includes_coverage_and_margin_summaries():
    rows = [
        {"text": "bank account security notice", "label": "legitimate"},
        {"text": "win a free prize today", "label": "spam"},
        {"text": "unseen nebula vocabulary", "label": "scam"},
    ]

    report = build_feature_error_report(rows, make_pipeline())

    assert "mean_vocabulary_coverage_correct" in report
    assert "mean_vocabulary_coverage_errors" in report
    assert "mean_top_score_margin_correct" in report
    assert "mean_top_score_margin_errors" in report
    assert set(report["by_actual_label"]) == {"legitimate", "scam", "spam"}


def test_feature_report_rejects_empty_rows():
    with pytest.raises(ValueError, match="must not be empty"):
        build_feature_error_report([], make_pipeline())


def test_feature_report_rejects_pipeline_without_expected_steps():
    class InvalidPipeline:
        named_steps = {}

    with pytest.raises(ValueError, match="named 'tfidf' and 'classifier'"):
        build_feature_error_report(
            [{"text": "hello there", "label": "legitimate"}],
            InvalidPipeline(),
        )
