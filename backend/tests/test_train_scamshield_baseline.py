import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from train_scamshield_baseline import (
    LABEL_ORDER,
    build_pipeline,
    calculate_metrics,
    group_metrics,
    read_split,
    run_experiment,
    validate_splits,
)


def text_hash(text):
    normalized = " ".join(text.casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def make_rows(per_class=8, language="english", start=0):
    rows = []
    index = start
    phrases = {
        "legitimate": "Your appointment confirmation is available",
        "spam": "Special promotional offer shop today",
        "scam": "Urgent fake KYC account blocked share OTP",
    }
    for label in LABEL_ORDER:
        for number in range(per_class):
            index += 1
            text = f"{phrases[label]} reference code {index}"
            rows.append({
                "model_row_id": f"SS_{index:06d}",
                "text": text,
                "label": label,
                "label_provenance": "provisional_silver_test_fixture",
                "masked_text_sha256": text_hash(text),
                "languages_json": json.dumps([language]),
                "source_datasets_json": json.dumps(["Fixture_Source"]),
            })
    return rows


def write_split(path, rows):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_metrics_return_all_three_classes_and_false_positive_rates():
    y_true = ["legitimate", "legitimate", "spam", "spam", "scam", "scam"]
    y_pred = ["legitimate", "spam", "spam", "scam", "scam", "scam"]

    metrics = calculate_metrics(y_true, y_pred)

    assert metrics["confusion_matrix_labels"] == list(LABEL_ORDER)
    assert metrics["accuracy"] == pytest.approx(4 / 6)
    assert set(metrics["class_metrics"]) == set(LABEL_ORDER)
    assert metrics["class_metrics"]["scam"]["recall"] == pytest.approx(1.0)
    assert 0.0 <= metrics["class_metrics"]["scam"]["false_positive_rate"] <= 1.0


def test_metrics_reject_mismatched_or_empty_predictions():
    with pytest.raises(ValueError, match="must match and be non-empty"):
        calculate_metrics([], [])
    with pytest.raises(ValueError, match="must match and be non-empty"):
        calculate_metrics(["scam"], [])


def test_group_metrics_reports_language_and_source_support():
    rows = make_rows(per_class=3)
    for row in rows:
        row["_language"] = "hindi"
        row["_sources"] = ["Fixture_Source"]
    predictions = [row["label"] for row in rows]

    by_language = group_metrics(rows, predictions, "_language")
    by_source = group_metrics(rows, predictions, "_sources")

    assert by_language["hindi"]["class_support"] == {
        "legitimate": 3, "spam": 3, "scam": 3
    }
    assert by_source["Fixture_Source"]["rows"] == 9
    assert by_source["Fixture_Source"]["metrics"]["macro_f1"] == pytest.approx(1.0)


def test_read_split_validates_hash_and_metadata(tmp_path):
    rows = make_rows(per_class=1)
    path = tmp_path / "scamshield_train.csv"
    write_split(path, rows)

    loaded = read_split(path)

    assert len(loaded) == len(LABEL_ORDER)
    assert all(row["_language"] == "english" for row in loaded)
    assert all(row["_sources"] == ["Fixture_Source"] for row in loaded)


def test_read_split_rejects_masked_text_hash_mismatch(tmp_path):
    rows = make_rows(per_class=1)
    rows[0]["masked_text_sha256"] = "0" * 64
    path = tmp_path / "scamshield_train.csv"
    write_split(path, rows)

    with pytest.raises(ValueError, match="hash mismatch"):
        read_split(path)


def test_read_split_rejects_unmapped_label(tmp_path):
    rows = make_rows(per_class=1)
    rows[0]["label"] = "needs_review"
    path = tmp_path / "scamshield_train.csv"
    write_split(path, rows)

    with pytest.raises(ValueError, match="unsupported label"):
        read_split(path)


def test_read_split_rejects_conflicting_language_metadata(tmp_path):
    rows = make_rows(per_class=1)
    rows[0]["languages_json"] = '["english", "hindi"]'
    path = tmp_path / "scamshield_train.csv"
    write_split(path, rows)

    with pytest.raises(ValueError, match="conflicting language tags"):
        read_split(path)


def test_read_split_rejects_missing_file_with_preparation_hint(tmp_path):
    with pytest.raises(FileNotFoundError, match="split_scamshield_candidate.py"):
        read_split(tmp_path / "missing.csv")


def test_validate_splits_rejects_missing_class():
    train = make_rows(per_class=2)
    validation = make_rows(per_class=2, start=100)
    validation = [row for row in validation if row["label"] != "scam"]
    test = make_rows(per_class=2, start=200)

    for rows in (train, validation, test):
        for row in rows:
            row["_language"] = "english"
            row["_sources"] = ["Fixture_Source"]

    with pytest.raises(ValueError, match="must contain all three classes"):
        validate_splits({
            "train": train, "validation": validation, "test": test
        })


def test_validate_splits_rejects_exact_hash_leakage():
    train = make_rows(per_class=2)
    validation = make_rows(per_class=2, start=100)
    test = make_rows(per_class=2, start=200)
    validation[0]["masked_text_sha256"] = train[0]["masked_text_sha256"]

    for rows in (train, validation, test):
        for row in rows:
            row["_language"] = "english"
            row["_sources"] = ["Fixture_Source"]

    with pytest.raises(ValueError, match="Exact masked text appears"):
        validate_splits({
            "train": train, "validation": validation, "test": test
        })


def test_validate_splits_allows_separate_unique_partitions():
    train = make_rows(per_class=2)
    validation = make_rows(per_class=2, start=100)
    test = make_rows(per_class=2, start=200)
    splits = {"train": train, "validation": validation, "test": test}

    for rows in splits.values():
        for row in rows:
            row["_language"] = "english"
            row["_sources"] = ["Fixture_Source"]

    validate_splits(splits)


def test_pipeline_uses_character_tfidf_and_balanced_logistic_regression():
    pipeline = build_pipeline()

    assert pipeline.named_steps["tfidf"].analyzer == "char"
    assert pipeline.named_steps["tfidf"].ngram_range == (2, 5)
    assert pipeline.named_steps["classifier"].class_weight == "balanced"
    assert pipeline.named_steps["classifier"].max_iter == 2000


def test_validation_only_run_does_not_open_test_file_and_saves_model(tmp_path):
    split_dir = tmp_path / "splits"
    artifact_dir = tmp_path / "artifacts"
    split_dir.mkdir()

    train = make_rows(per_class=12)
    validation = make_rows(per_class=4, start=1000)
    write_split(split_dir / "scamshield_train.csv", train)
    write_split(split_dir / "scamshield_validation.csv", validation)
    # Deliberately do not create a test file. Validation-only must not open it.

    report = run_experiment(
        split_directory=split_dir,
        artifact_directory=artifact_dir,
        validation_only=True,
    )

    assert report["test_evaluated"] is False
    assert report["model_artifact_saved"] is True
    assert report["validation_metrics"]["macro_f1"] >= 0.0
    assert (artifact_dir / "scamshield_three_class_char_tfidf_logistic.joblib").is_file()
    assert (artifact_dir / "scamshield_three_class_baseline_metrics.json").is_file()


def test_run_experiment_evaluates_test_only_when_requested_by_default(tmp_path):
    split_dir = tmp_path / "splits"
    artifact_dir = tmp_path / "artifacts"
    split_dir.mkdir()

    train = make_rows(per_class=12)
    validation = make_rows(per_class=4, start=1000)
    test = make_rows(per_class=4, start=2000)
    write_split(split_dir / "scamshield_train.csv", train)
    write_split(split_dir / "scamshield_validation.csv", validation)
    write_split(split_dir / "scamshield_test.csv", test)

    report = run_experiment(
        split_directory=split_dir,
        artifact_directory=artifact_dir,
        validation_only=False,
    )

    assert report["test_evaluated"] is True
    assert set(report["test_metrics"]["class_metrics"]) == set(LABEL_ORDER)


def test_class_report_uses_only_message_text_in_pipeline():
    pipeline = build_pipeline()
    assert list(pipeline.named_steps) == ["tfidf", "classifier"]
