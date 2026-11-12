import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from ablate_multilingual_mask_markers import (
    build_ablation_report,
    strip_mask_markers,
)
from train_multilingual_baseline import build_pipeline


def make_row(text, label, language="english"):
    return {
        "text": text,
        "label": label,
        "language": language,
        "split": "train",
        "group_id": f"g-{len(text)}-{label}-{language}",
        "model_text_sha256": "test-hash",
    }


def sample_data():
    train = [
        make_row("Your normal bank balance reminder is ready [LONG_NUMBER]", "ham"),
        make_row("A family meeting is planned for tomorrow [12_DIGIT_NUMBER]", "ham"),
        make_row("Your library book is due next week", "ham"),
        make_row("The school event begins at nine today", "ham"),
        make_row("Urgent send your otp using [URL] to unlock account", "scam"),
        make_row("Claim a reward by paying [LONG_NUMBER] processing fee", "scam"),
        make_row("Verify your upi account at [DOMAIN] immediately", "scam"),
        make_row("Your wallet is blocked click [URL] to restore access", "scam"),
    ]
    validation = [
        make_row("Your bank account reminder is ready [LONG_NUMBER]", "ham"),
        make_row("Family meeting is planned for next week", "ham"),
        make_row("Library book return reminder for tomorrow", "ham"),
        make_row("School event begins this morning", "ham"),
        make_row("Urgent share otp through [URL] now", "scam"),
        make_row("Claim reward after paying [LONG_NUMBER] fee", "scam"),
        make_row("Verify upi profile through [DOMAIN] now", "scam"),
        make_row("Wallet is blocked click [URL] immediately", "scam"),
    ]
    for row in validation:
        row["split"] = "validation"
    return train, validation


def test_strip_mask_markers_removes_all_soul_placeholders():
    text = (
        "Visit [URL] [DOMAIN] [EMAIL_OR_UPI] [PAN_LIKE] "
        "[12_DIGIT_NUMBER] [LONG_NUMBER] now"
    )

    result = strip_mask_markers(text)

    assert result == "Visit now"


def test_strip_mask_markers_is_case_insensitive_and_preserves_other_text():
    assert strip_mask_markers("Read URL policy; [url] is hidden") == (
        "Read URL policy; is hidden"
    )


def test_strip_mask_markers_normalises_whitespace():
    assert strip_mask_markers("A [URL]   B") == "A B"


def test_ablation_report_is_validation_only_and_preserves_original_model():
    train, validation = sample_data()
    original_model = build_pipeline()
    original_model.fit(
        [row["text"] for row in train],
        [row["label"] for row in train],
    )
    predictions_before = original_model.predict([row["text"] for row in validation])

    report = build_ablation_report(train, validation, original_model)

    predictions_after = original_model.predict([row["text"] for row in validation])
    assert predictions_after.tolist() == predictions_before.tolist()
    assert report["test_partition_read"] is False
    assert report["original_model_retrained"] is False
    assert report["original_model_artifact_modified"] is False
    assert report["ablation_model_saved"] is False
    assert report["train_rows"] == len(train)
    assert report["validation_rows"] == len(validation)
    assert set(report["language_comparison"]) == {"english"}


def test_ablation_report_contains_aggregate_and_language_deltas():
    train, validation = sample_data()
    original_model = build_pipeline().fit(
        [row["text"] for row in train],
        [row["label"] for row in train],
    )

    report = build_ablation_report(train, validation, original_model)

    assert set(report["aggregate_metric_delta_without_markers_minus_original"]) == {
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
    }
    language = report["language_comparison"]["english"]
    assert language["rows"] == len(validation)
    assert "accuracy_delta" in language
    assert "scam_recall_delta" in language


def test_ablation_report_rejects_empty_partitions():
    train, validation = sample_data()
    model = build_pipeline().fit(
        [row["text"] for row in train],
        [row["label"] for row in train],
    )

    with pytest.raises(ValueError, match="must both be non-empty"):
        build_ablation_report([], validation, model)


def test_ablation_report_rejects_text_that_becomes_empty_after_stripping():
    train, validation = sample_data()
    train[0]["text"] = "[URL]"
    model = build_pipeline().fit(
        [row["text"] for row in train],
        [row["label"] for row in train],
    )

    with pytest.raises(ValueError, match="produced an empty message"):
        build_ablation_report(train, validation, model)
