import sys
from pathlib import Path

import pytest


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from train_multilingual_baseline import (
    LABEL_ORDER,
    build_pipeline,
    calculate_language_metrics,
    calculate_metrics,
    count_language_labels,
    read_split,
    sha256_text,
    validate_splits,
)


def make_row(text, label, split, language="english", group_id=None):
    digest = sha256_text(text)
    return {
        "text": text,
        "label": label,
        "language": language,
        "split": split,
        "group_id": group_id or f"G_{digest[:12]}",
        "model_text_sha256": digest,
    }


def valid_splits():
    return {
        "train": [
            make_row("normal message alpha", "ham", "train"),
            make_row("urgent scam alpha", "scam", "train"),
            make_row("normal message beta", "ham", "train"),
            make_row("urgent scam beta", "scam", "train"),
        ],
        "validation": [
            make_row("normal message gamma", "ham", "validation"),
            make_row("urgent scam gamma", "scam", "validation"),
        ],
        "test": [
            make_row("normal message delta", "ham", "test"),
            make_row("urgent scam delta", "scam", "test"),
        ],
    }


def test_pipeline_uses_character_ngrams_and_balanced_logistic_regression():
    pipeline = build_pipeline()

    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]

    assert vectorizer.analyzer == "char"
    assert vectorizer.ngram_range == (2, 5)
    assert vectorizer.min_df == 2
    assert vectorizer.max_features == 150000
    assert classifier.class_weight == "balanced"
    assert classifier.max_iter == 2000


def test_metrics_include_binary_class_fpr_and_confusion_matrix():
    y_true = ["ham", "ham", "scam", "scam"]
    y_pred = ["ham", "scam", "scam", "ham"]

    metrics = calculate_metrics(y_true, y_pred)

    assert metrics["accuracy"] == pytest.approx(0.5)
    assert metrics["balanced_accuracy"] == pytest.approx(0.5)
    assert metrics["macro_f1"] == pytest.approx(0.5)
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["confusion_matrix_labels"] == list(LABEL_ORDER)
    assert metrics["class_metrics"]["ham"]["false_positive_rate"] == pytest.approx(0.5)
    assert metrics["class_metrics"]["scam"]["false_positive_rate"] == pytest.approx(0.5)


def test_metrics_reject_empty_or_mismatched_inputs():
    with pytest.raises(ValueError, match="empty sample"):
        calculate_metrics([], [])
    with pytest.raises(ValueError, match="counts do not match"):
        calculate_metrics(["ham"], ["ham", "scam"])


def test_validate_splits_accepts_group_safe_splits():
    validate_splits(valid_splits())


def test_validate_splits_rejects_same_masked_text_across_partitions():
    splits = valid_splits()
    duplicate = dict(splits["train"][0])
    duplicate["split"] = "test"
    duplicate["group_id"] = "G_duplicate"
    splits["test"][0] = duplicate

    with pytest.raises(ValueError, match="Duplicate masked model text"):
        validate_splits(splits)


def test_validate_splits_rejects_group_id_across_partitions():
    splits = valid_splits()
    splits["test"][0]["group_id"] = splits["train"][0]["group_id"]

    with pytest.raises(ValueError, match="group appears across"):
        validate_splits(splits)


def test_validate_splits_rejects_missing_binary_class():
    splits = valid_splits()
    splits["validation"] = [
        row for row in splits["validation"] if row["label"] == "ham"
    ]

    with pytest.raises(ValueError, match="missing classes"):
        validate_splits(splits)


def test_validate_splits_rejects_language_missing_from_test():
    splits = valid_splits()
    splits["train"][0]["language"] = "hindi"

    with pytest.raises(ValueError, match="missing training languages"):
        validate_splits(splits)


def test_read_split_returns_only_model_and_evaluation_fields(tmp_path):
    text = "An ordinary sample message"
    digest = sha256_text(text)
    path = tmp_path / "train.csv"
    path.write_text(
        "record_id,text,source_label,language,split,group_id,"
        "model_text_sha256,source_dataset\n"
        f'M1,"{text}",ham,hindi,train,G1,{digest},synthetic\n',
        encoding="utf-8",
    )

    rows = read_split(path)

    assert rows == [
        {
            "text": text,
            "label": "ham",
            "language": "hindi",
            "split": "train",
            "group_id": "G1",
            "model_text_sha256": digest,
        }
    ]


def test_read_split_rejects_wrong_partition(tmp_path):
    text = "An ordinary sample message"
    path = tmp_path / "train.csv"
    path.write_text(
        "text,source_label,language,split,group_id,model_text_sha256\n"
        f'"{text}",ham,hindi,test,G1,{sha256_text(text)}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not 'train'"):
        read_split(path)


def test_read_split_rejects_hash_mismatch(tmp_path):
    path = tmp_path / "train.csv"
    path.write_text(
        "text,source_label,language,split,group_id,model_text_sha256\n"
        "normal,ham,hindi,train,G1,incorrect\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="sha256 mismatch"):
        read_split(path)


def test_read_split_rejects_unsupported_label(tmp_path):
    text = "ordinary message"
    path = tmp_path / "train.csv"
    path.write_text(
        "text,source_label,language,split,group_id,model_text_sha256\n"
        f'{text},spam,hindi,train,G1,{sha256_text(text)}\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported label"):
        read_split(path)


def test_language_metrics_mark_low_class_support_as_preliminary():
    rows = [
        make_row("ham one", "ham", "test", "odia"),
        make_row("ham two", "ham", "test", "odia"),
        make_row("scam one", "scam", "test", "odia"),
    ]

    metrics = calculate_language_metrics(rows, ["ham", "ham", "scam"])

    assert metrics["odia"]["low_support"] is True
    assert metrics["odia"]["label_support"] == {"ham": 2, "scam": 1}
    assert "fewer than 20" in metrics["odia"]["support_note"]


def test_language_metrics_do_not_mark_sufficient_support_as_low():
    rows = []
    predictions = []
    for index in range(20):
        rows.append(make_row(f"ham sample {index}", "ham", "test", "hindi"))
        predictions.append("ham")
        rows.append(make_row(f"scam sample {index}", "scam", "test", "hindi"))
        predictions.append("scam")

    metrics = calculate_language_metrics(rows, predictions)

    assert metrics["hindi"]["low_support"] is False
    assert metrics["hindi"]["label_support"] == {"ham": 20, "scam": 20}


def test_count_language_labels_returns_per_language_binary_counts():
    rows = [
        make_row("ham one", "ham", "train", "hindi"),
        make_row("scam one", "scam", "train", "hindi"),
        make_row("ham two", "ham", "train", "tamil"),
    ]

    counts = count_language_labels(rows)

    assert counts == {
        "hindi": {"ham": 1, "scam": 1},
        "tamil": {"ham": 1, "scam": 0},
    }
