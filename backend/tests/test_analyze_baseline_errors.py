import sys
from pathlib import Path

import pytest


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from analyze_baseline_errors import (
    build_error_rows,
    build_error_summary,
    save_error_csv,
)


def test_build_error_rows_keeps_only_wrong_predictions():
    rows = [
        {"text": "normal reminder", "label": "legitimate"},
        {"text": "prize offer", "label": "spam"},
        {"text": "account warning", "label": "scam"},
    ]
    predictions = ["legitimate", "scam", "scam"]
    probabilities = [
        [0.90, 0.05, 0.05],
        [0.10, 0.75, 0.15],
        [0.05, 0.90, 0.05],
    ]

    errors = build_error_rows(
        rows,
        predictions,
        probabilities,
        ["legitimate", "scam", "spam"],
    )

    assert len(errors) == 1
    assert errors[0]["validation_row"] == 3
    assert errors[0]["actual_label"] == "spam"
    assert errors[0]["predicted_label"] == "scam"
    assert errors[0]["top_class"] == "scam"
    assert errors[0]["top_class_probability"] == 0.75
    assert errors[0]["text"] == "prize offer"


def test_build_error_rows_rejects_different_input_lengths():
    with pytest.raises(ValueError, match="equal lengths"):
        build_error_rows(
            [{"text": "message", "label": "spam"}],
            [],
            [],
            ["legitimate", "scam", "spam"],
        )


def test_build_error_rows_rejects_probability_shape_mismatch():
    with pytest.raises(ValueError, match="do not match"):
        build_error_rows(
            [{"text": "message", "label": "spam"}],
            ["scam"],
            [[0.2, 0.8]],
            ["legitimate", "scam", "spam"],
        )


def test_build_error_summary_counts_only_off_diagonal_errors():
    actual = ["legitimate", "scam", "spam", "spam"]
    predicted = ["legitimate", "spam", "scam", "spam"]

    summary = build_error_summary(actual, predicted)

    assert summary["total_rows"] == 4
    assert summary["correct_rows"] == 2
    assert summary["misclassified_rows"] == 2
    assert summary["confusion_matrix"] == [
        [1, 0, 0],
        [0, 0, 1],
        [0, 1, 1],
    ]
    assert summary["error_pairs"] == [
        {"actual": "scam", "predicted": "spam", "count": 1},
        {"actual": "spam", "predicted": "scam", "count": 1},
    ]
    assert summary["split"] == "validation_only"


def test_build_error_summary_rejects_length_mismatch():
    with pytest.raises(ValueError, match="equal lengths"):
        build_error_summary(["spam"], [])


def test_build_error_summary_rejects_empty_validation_data():
    with pytest.raises(ValueError, match="must not be empty"):
        build_error_summary([], [])


def test_save_error_csv_writes_local_message_level_fields(tmp_path):
    path = tmp_path / "errors.csv"
    errors = [
        {
            "validation_row": 3,
            "actual_label": "spam",
            "predicted_label": "scam",
            "top_class": "scam",
            "top_class_probability": 0.75,
            "text": "masked message",
        }
    ]

    save_error_csv(path, errors)

    content = path.read_text(encoding="utf-8")
    assert "actual_label,predicted_label" in content
    assert "masked message" in content
    assert "spam,scam,scam,0.75" in content



def test_save_error_csv_neutralizes_formula_like_message_text(tmp_path):
    path = tmp_path / "errors.csv"
    errors = [
        {
            "validation_row": 2,
            "actual_label": "spam",
            "predicted_label": "scam",
            "top_class": "scam",
            "top_class_probability": 0.8,
            "text": "  =HYPERLINK(\"https://example.invalid\")",
        }
    ]

    save_error_csv(path, errors)

    content = path.read_text(encoding="utf-8")
    assert "'  =HYPERLINK(" in content
