import sys
from pathlib import Path

import pytest


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from train_text_baseline import (
    LABEL_ORDER,
    build_pipeline,
    calculate_metrics,
    read_split,
    validate_splits,
)


def make_row(text, label, split):
    return {"text": text, "label": label, "split": split}


def valid_splits():
    return {
        "train": [
            make_row("legitimate reminder one", "legitimate", "train"),
            make_row("scam account warning one", "scam", "train"),
            make_row("spam offer message one", "spam", "train"),
        ],
        "validation": [
            make_row("legitimate reminder two", "legitimate", "validation"),
            make_row("scam account warning two", "scam", "validation"),
            make_row("spam offer message two", "spam", "validation"),
        ],
        "test": [
            make_row("legitimate reminder three", "legitimate", "test"),
            make_row("scam account warning three", "scam", "test"),
            make_row("spam offer message three", "spam", "test"),
        ],
    }


def test_pipeline_uses_tfidf_and_balanced_logistic_regression():
    pipeline = build_pipeline()

    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]

    assert vectorizer.ngram_range == (1, 2)
    assert vectorizer.min_df == 2
    assert vectorizer.max_features == 50000
    assert classifier.class_weight == "balanced"
    assert classifier.max_iter == 2000


def test_metrics_include_per_class_fpr_and_confusion_matrix():
    y_true = [
        "legitimate", "legitimate",
        "scam", "scam",
        "spam", "spam",
    ]
    y_pred = [
        "legitimate", "scam",
        "scam", "spam",
        "spam", "legitimate",
    ]

    metrics = calculate_metrics(y_true, y_pred)

    assert metrics["accuracy"] == pytest.approx(0.5)
    assert metrics["balanced_accuracy"] == pytest.approx(0.5)
    assert metrics["macro_f1"] == pytest.approx(0.5)
    assert metrics["confusion_matrix"] == [
        [1, 1, 0],
        [0, 1, 1],
        [1, 0, 1],
    ]
    for label in LABEL_ORDER:
        assert metrics["class_metrics"][label]["false_positive_rate"] == pytest.approx(0.25)


def test_validate_splits_accepts_non_overlapping_texts():
    validate_splits(valid_splits())


def test_validate_splits_rejects_identical_text_across_partitions():
    splits = valid_splits()
    splits["test"][0]["text"] = splits["train"][0]["text"]

    with pytest.raises(ValueError, match="Duplicate normalised model text"):
        validate_splits(splits)


def test_validate_splits_rejects_missing_class():
    splits = valid_splits()
    splits["validation"] = [
        row for row in splits["validation"] if row["label"] != "spam"
    ]

    with pytest.raises(ValueError, match="missing classes"):
        validate_splits(splits)


def test_read_split_uses_expected_split_and_returns_only_text_and_label(tmp_path):
    path = tmp_path / "train.csv"
    path.write_text(
        "record_id,label,text,split,split_group_id,source_occurrences\n"
        'M1,legitimate,"A normal reminder",train,G1,1\n',
        encoding="utf-8",
    )

    rows = read_split(path)

    assert rows == [{"text": "A normal reminder", "label": "legitimate"}]


def test_read_split_rejects_row_from_wrong_partition(tmp_path):
    path = tmp_path / "train.csv"
    path.write_text(
        "record_id,label,text,split\n"
        'M1,legitimate,"A normal reminder",test\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not 'train'"):
        read_split(path)
