import sys
from pathlib import Path

import pytest


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from build_validation_label_review_queue import build_review_records


def make_validation_row(record_id="S00001", label="scam", text="masked text"):
    return {
        "record_id": record_id,
        "label": label,
        "text": text,
        "split": "validation",
    }


def make_error_row(actual="scam", predicted="spam", text="masked text"):
    return {
        "validation_row": "2",
        "actual_label": actual,
        "predicted_label": predicted,
        "top_class_probability": "0.82",
        "text": text,
    }


def make_prepared_row(
    source_label="smishing",
    label="scam",
    text="masked text",
    occurrences="1",
):
    return {
        "source_label": source_label,
        "label": label,
        "text": text,
        "source_occurrences": occurrences,
        "soul_label": "",
        "review_status": "pending",
        "annotation_note": "",
    }


def test_build_review_records_hides_labels_and_predictions_from_blind_queue():
    blind, key = build_review_records(
        [make_error_row()],
        [make_validation_row()],
        [make_prepared_row()],
    )

    assert blind == [
        {
            "review_id": "S00001",
            "text": "masked text",
            "soul_label": "",
            "review_status": "pending",
            "annotation_note": "",
        }
    ]
    assert "source_label" not in blind[0]
    assert "baseline_label" not in blind[0]
    assert "model_prediction" not in blind[0]
    assert key == [
        {
            "review_id": "S00001",
            "source_label": "smishing",
            "baseline_label": "scam",
            "model_prediction": "spam",
            "top_class_probability": 0.82,
            "source_occurrences": 1,
        }
    ]
    assert "text" not in key[0]


def test_build_review_records_sums_repeated_source_occurrences():
    blind, key = build_review_records(
        [make_error_row()],
        [make_validation_row()],
        [
            make_prepared_row(occurrences="2"),
            make_prepared_row(occurrences="3"),
        ],
    )

    assert len(blind) == 1
    assert key[0]["source_occurrences"] == 5


def test_build_review_records_rejects_ambiguous_source_provenance():
    with pytest.raises(ValueError, match="multiple source labels"):
        build_review_records(
            [make_error_row()],
            [make_validation_row()],
            [
                make_prepared_row(source_label="smishing"),
                make_prepared_row(source_label="spam", label="spam"),
            ],
        )


def test_build_review_records_rejects_text_mismatch():
    with pytest.raises(ValueError, match="does not match validation"):
        build_review_records(
            [make_error_row(text="different text")],
            [make_validation_row()],
            [make_prepared_row()],
        )


def test_build_review_records_rejects_actual_label_mismatch():
    with pytest.raises(ValueError, match="actual label"):
        build_review_records(
            [make_error_row(actual="legitimate")],
            [make_validation_row()],
            [make_prepared_row()],
        )


def test_build_review_records_rejects_prediction_that_is_not_an_error():
    with pytest.raises(ValueError, match="valid misclassification"):
        build_review_records(
            [make_error_row(actual="scam", predicted="scam")],
            [make_validation_row()],
            [make_prepared_row()],
        )


def test_build_review_records_rejects_rows_outside_validation_partition():
    row = make_validation_row()
    row["split"] = "test"

    with pytest.raises(ValueError, match="not in the validation split"):
        build_review_records(
            [make_error_row()],
            [row],
            [make_prepared_row()],
        )


def test_build_review_records_rejects_source_mapping_inconsistent_with_baseline():
    with pytest.raises(ValueError, match="does not match the frozen"):
        build_review_records(
            [make_error_row()],
            [make_validation_row()],
            [make_prepared_row(source_label="ham", label="legitimate")],
        )


def test_build_review_records_rejects_duplicate_validation_row_numbers():
    errors = [
        make_error_row(),
        make_error_row(),
    ]

    with pytest.raises(ValueError, match="Duplicate validation_row"):
        build_review_records(
            errors,
            [make_validation_row(), make_validation_row("S00002", "spam", "other")],
            [
                make_prepared_row(),
                make_prepared_row(source_label="spam", label="spam", text="other"),
            ],
        )


def test_build_review_records_rejects_invalid_score():
    error = make_error_row()
    error["top_class_probability"] = "1.5"

    with pytest.raises(ValueError, match="between 0 and 1"):
        build_review_records(
            [error],
            [make_validation_row()],
            [make_prepared_row()],
        )


def test_build_review_records_rejects_missing_prepared_text_match():
    with pytest.raises(ValueError, match="Could not match"):
        build_review_records(
            [make_error_row()],
            [make_validation_row()],
            [make_prepared_row(text="another masked message")],
        )
