"""Train a separate exploratory binary multilingual SMS baseline.

This experiment uses the synthetic 14-language scam/ham candidate only. It is
kept separate from the frozen three-class Mendeley baseline and API artifact.

Run from the repository root:
    python data/train_multilingual_baseline.py

Only message text is used as a model feature. The language field is retained
solely for subgroup evaluation; it is not passed to the classifier. Model and
metrics outputs stay under the Git-ignored data/private/ directory.
"""

import csv
import hashlib
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline


DATA_DIRECTORY = Path(__file__).resolve().parent
SPLIT_DIRECTORY = (
    DATA_DIRECTORY
    / "private"
    / "multilingual_candidates"
    / "prepared"
    / "splits"
)
ARTIFACT_DIRECTORY = DATA_DIRECTORY / "private" / "model_artifacts"
MODEL_PATH = ARTIFACT_DIRECTORY / "multilingual_char_tfidf_logistic_regression.joblib"
METRICS_PATH = ARTIFACT_DIRECTORY / "multilingual_baseline_metrics.json"

LABEL_ORDER = ("ham", "scam")
SPLIT_NAMES = ("train", "validation", "test")
MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION = 20

VECTORIZER_CONFIG = {
    "analyzer": "char",
    "ngram_range": [2, 5],
    "min_df": 2,
    "max_features": 150000,
    "sublinear_tf": True,
    "lowercase": True,
}
CLASSIFIER_CONFIG = {
    "class_weight": "balanced",
    "max_iter": 2000,
    "random_state": 42,
}


def normalise_text(text):
    """Normalise whitespace and case for integrity checks."""
    return " ".join((text or "").casefold().split())


def sha256_text(text):
    return hashlib.sha256(normalise_text(text).encode("utf-8")).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_split(path):
    """Read model text, binary label and subgroup metadata."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Multilingual split not found: {path}. "
            "Run data/prepare_multilingual_candidate.py first."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {
            "text",
            "source_label",
            "language",
            "split",
            "group_id",
            "model_text_sha256",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path.name} is missing columns: "
                + ", ".join(sorted(missing))
            )

        rows = []
        expected_split = path.stem.casefold()
        for row_number, row in enumerate(reader, start=2):
            text = (row.get("text") or "").strip()
            label = (row.get("source_label") or "").strip().casefold()
            language = (row.get("language") or "").strip().casefold()
            split = (row.get("split") or "").strip().casefold()
            group_id = (row.get("group_id") or "").strip()
            text_hash = (row.get("model_text_sha256") or "").strip()

            if not text:
                raise ValueError(
                    f"{path.name} contains blank text at row {row_number}."
                )
            if label not in LABEL_ORDER:
                raise ValueError(
                    f"{path.name} contains unsupported label {label!r} "
                    f"at row {row_number}."
                )
            if not language:
                raise ValueError(
                    f"{path.name} contains a blank language at row {row_number}."
                )
            if split != expected_split:
                raise ValueError(
                    f"{path.name} contains a row assigned to {split!r}, "
                    f"not {expected_split!r}."
                )
            if not group_id or not text_hash:
                raise ValueError(
                    f"{path.name} contains a blank group/hash at row {row_number}."
                )
            if sha256_text(text) != text_hash:
                raise ValueError(
                    f"{path.name} has a model_text_sha256 mismatch "
                    f"at row {row_number}."
                )

            rows.append(
                {
                    "text": text,
                    "label": label,
                    "language": language,
                    "split": split,
                    "group_id": group_id,
                    "model_text_sha256": text_hash,
                }
            )

    if not rows:
        raise ValueError(f"{path.name} contains no data rows.")
    return rows


def validate_splits(splits):
    """Check labels, group separation and exact-text uniqueness."""
    seen_groups = {}
    seen_texts = {}
    language_sets = {}

    for split_name in SPLIT_NAMES:
        if split_name not in splits or not splits[split_name]:
            raise ValueError(f"The {split_name} split is empty.")

        labels = {row["label"] for row in splits[split_name]}
        missing_labels = set(LABEL_ORDER) - labels
        if missing_labels:
            raise ValueError(
                f"The {split_name} split is missing classes: "
                + ", ".join(sorted(missing_labels))
            )

        language_sets[split_name] = {
            row["language"] for row in splits[split_name]
        }

        for row in splits[split_name]:
            group_id = row["group_id"]
            text_hash = row["model_text_sha256"]

            if group_id in seen_groups and seen_groups[group_id] != split_name:
                raise ValueError(
                    "A masked-text group appears across multiple partitions."
                )
            seen_groups[group_id] = split_name

            if text_hash in seen_texts:
                previous_split = seen_texts[text_hash]
                raise ValueError(
                    "Duplicate masked model text detected in "
                    f"{previous_split!r} and {split_name!r}."
                )
            seen_texts[text_hash] = split_name

    for split_name in ("validation", "test"):
        missing_languages = language_sets["train"] - language_sets[split_name]
        if missing_languages:
            raise ValueError(
                f"The {split_name} split is missing training languages: "
                + ", ".join(sorted(missing_languages))
            )


def build_pipeline():
    """Build a fixed character n-gram TF-IDF + Logistic Regression baseline."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(2, 5),
                    min_df=2,
                    max_features=150000,
                    sublinear_tf=True,
                    lowercase=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


def calculate_metrics(y_true, y_pred):
    """Calculate binary aggregate and one-vs-rest class metrics."""
    if not y_true:
        raise ValueError("Cannot calculate metrics for an empty sample.")
    if len(y_true) != len(y_pred):
        raise ValueError("True and predicted label counts do not match.")

    matrix = confusion_matrix(y_true, y_pred, labels=list(LABEL_ORDER))
    report = classification_report(
        y_true,
        y_pred,
        labels=list(LABEL_ORDER),
        output_dict=True,
        zero_division=0,
    )

    total = int(matrix.sum())
    class_metrics = {}

    for index, label in enumerate(LABEL_ORDER):
        true_positive = int(matrix[index, index])
        false_positive = int(matrix[:, index].sum() - true_positive)
        false_negative = int(matrix[index, :].sum() - true_positive)
        true_negative = total - true_positive - false_positive - false_negative
        denominator = false_positive + true_negative
        false_positive_rate = (
            false_positive / denominator if denominator else 0.0
        )

        class_metrics[label] = {
            "precision": float(report[label]["precision"]),
            "recall": float(report[label]["recall"]),
            "f1": float(report[label]["f1-score"]),
            "support": int(report[label]["support"]),
            "false_positive_rate": float(false_positive_rate),
        }

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(
            f1_score(
                y_true,
                y_pred,
                labels=list(LABEL_ORDER),
                average="macro",
                zero_division=0,
            )
        ),
        "weighted_f1": float(
            f1_score(
                y_true,
                y_pred,
                labels=list(LABEL_ORDER),
                average="weighted",
                zero_division=0,
            )
        ),
        "class_metrics": class_metrics,
        "confusion_matrix": matrix.astype(int).tolist(),
        "confusion_matrix_labels": list(LABEL_ORDER),
    }


def calculate_language_metrics(rows, predictions):
    """Evaluate each language separately, marking low-support estimates."""
    if len(rows) != len(predictions):
        raise ValueError("Rows and predictions counts do not match.")

    grouped = defaultdict(lambda: {"true": [], "predicted": []})
    for row, prediction in zip(rows, predictions):
        language = row["language"]
        grouped[language]["true"].append(row["label"])
        grouped[language]["predicted"].append(prediction)

    output = {}
    for language in sorted(grouped):
        y_true = grouped[language]["true"]
        y_pred = grouped[language]["predicted"]
        support = Counter(y_true)
        low_support_labels = [
            label
            for label in LABEL_ORDER
            if support.get(label, 0) < MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION
        ]

        output[language] = {
            "rows": len(y_true),
            "label_support": {
                label: int(support.get(label, 0)) for label in LABEL_ORDER
            },
            "metrics": calculate_metrics(y_true, y_pred),
            "low_support": bool(low_support_labels),
            "support_note": (
                "Preliminary only: fewer than "
                f"{MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION} test examples "
                "for " + ", ".join(low_support_labels) + "."
                if low_support_labels
                else "At least "
                f"{MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION} examples "
                "for each class in this split."
            ),
        }

    return output


def count_language_labels(rows):
    counts = Counter((row["language"], row["label"]) for row in rows)
    return {
        language: {
            label: int(counts.get((language, label), 0))
            for label in LABEL_ORDER
        }
        for language in sorted({row["language"] for row in rows})
    }


def print_metrics(split_name, metrics, language_metrics):
    print(f"\n{split_name.upper()} OVERALL METRICS")
    print(f"  Accuracy:          {metrics['accuracy']:.4f}")
    print(f"  Balanced accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"  Macro F1:          {metrics['macro_f1']:.4f}")
    print(f"  Weighted F1:       {metrics['weighted_f1']:.4f}")

    print("\n  Per-class metrics:")
    print("  CLASS  PRECISION  RECALL  F1      FPR     SUPPORT")
    for label in LABEL_ORDER:
        values = metrics["class_metrics"][label]
        print(
            f"  {label:<6} "
            f"{values['precision']:>9.4f} "
            f"{values['recall']:>7.4f} "
            f"{values['f1']:>7.4f} "
            f"{values['false_positive_rate']:>7.4f} "
            f"{values['support']:>8}"
        )

    print("\n  Per-language metrics (language is evaluation-only metadata):")
    print("  LANGUAGE      HAM  SCAM  ACCURACY  SCAM_RECALL  SCAM_F1  NOTE")
    for language, values in language_metrics.items():
        label_support = values["label_support"]
        scam_metrics = values["metrics"]["class_metrics"]["scam"]
        note = "LOW SUPPORT" if values["low_support"] else "ok"
        print(
            f"  {language:<12} "
            f"{label_support['ham']:>4} "
            f"{label_support['scam']:>5} "
            f"{values['metrics']['accuracy']:>9.4f} "
            f"{scam_metrics['recall']:>11.4f} "
            f"{scam_metrics['f1']:>8.4f}  {note}"
        )


def main():
    split_paths = {
        name: SPLIT_DIRECTORY / f"{name}.csv"
        for name in SPLIT_NAMES
    }

    try:
        splits = {
            name: read_split(path)
            for name, path in split_paths.items()
        }
        validate_splits(splits)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(
            f"Multilingual baseline input validation failed: {error}"
        ) from error

    train_texts = [row["text"] for row in splits["train"]]
    train_labels = [row["label"] for row in splits["train"]]

    print("SOUL — multilingual character n-gram baseline")
    print("Task: synthetic binary scam vs ham")
    print("Model input: message text only")
    print("Language metadata: evaluation only; not a model feature")
    print("Training rows:", len(train_texts))
    print("Validation rows:", len(splits["validation"]))
    print("Test rows:", len(splits["test"]))
    print("Train class counts:", dict(Counter(train_labels)))
    print("Scikit-learn:", sklearn.__version__)
    print("Python:", platform.python_version())

    pipeline = build_pipeline()
    pipeline.fit(train_texts, train_labels)

    validation_true = [row["label"] for row in splits["validation"]]
    validation_texts = [row["text"] for row in splits["validation"]]
    validation_predictions = pipeline.predict(validation_texts)
    validation_metrics = calculate_metrics(
        validation_true,
        validation_predictions,
    )
    validation_by_language = calculate_language_metrics(
        splits["validation"],
        validation_predictions,
    )

    # Initial fixed-recipe holdout evaluation. Do not tune against this set.
    test_true = [row["label"] for row in splits["test"]]
    test_texts = [row["text"] for row in splits["test"]]
    test_predictions = pipeline.predict(test_texts)
    test_metrics = calculate_metrics(test_true, test_predictions)
    test_by_language = calculate_language_metrics(
        splits["test"],
        test_predictions,
    )

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH, compress=3)

    metadata = {
        "experiment": "separate_synthetic_14_language_binary_pilot",
        "model": "character n-gram TF-IDF + Logistic Regression",
        "source_dataset": "anmolshrivastav/scam_ham_india_14_languages",
        "source_type": "synthetic",
        "task": "binary scam_vs_ham",
        "labels": list(LABEL_ORDER),
        "model_input": "message_text_only",
        "language_metadata_usage": "evaluation_only_not_a_model_feature",
        "random_state": 42,
        "vectorizer_config": VECTORIZER_CONFIG,
        "classifier_config": CLASSIFIER_CONFIG,
        "minimum_class_support_for_interpretation": (
            MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION
        ),
        "scikit_learn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "split_sha256": {
            name: sha256_file(path)
            for name, path in split_paths.items()
        },
        "split_sizes": {
            name: len(splits[name]) for name in SPLIT_NAMES
        },
        "split_language_label_counts": {
            name: count_language_labels(splits[name])
            for name in SPLIT_NAMES
        },
        "validation_metrics": validation_metrics,
        "validation_metrics_by_language": validation_by_language,
        "test_metrics": test_metrics,
        "test_metrics_by_language": test_by_language,
        "test_set_policy": (
            "Initial fixed-recipe holdout evaluation only. Do not use test "
            "results to tune features, hyperparameters or thresholds."
        ),
        "limitations": [
            "The candidate is synthetic and does not establish real-world performance.",
            "The task is binary scam_vs_ham, not SOUL's three-class task.",
            "Language metadata is not a model input; subgroup metrics use it only for evaluation.",
            "Odia and Tamil have fewer than 20 scam examples in the test partition; interpret those subgroup metrics as preliminary.",
            "Exact-text grouping does not guarantee campaign-independent evaluation.",
            "Regex masking is not proof of anonymisation.",
            "This experiment does not alter the historical Mendeley model or its test set.",
        ],
    }

    with METRICS_PATH.open("w", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2, ensure_ascii=False)

    print_metrics("validation", validation_metrics, validation_by_language)
    print_metrics("test (initial holdout)", test_metrics, test_by_language)

    vectorizer = pipeline.named_steps["tfidf"]
    print("\nModel artifacts saved locally:")
    print("  Character features:", len(vectorizer.vocabulary_))
    print("  Model:", MODEL_PATH)
    print("  Metrics:", METRICS_PATH)
    print(
        "\nImportant: This is an exploratory synthetic binary baseline. "
        "Do not describe its scores as real-world fraud-detection accuracy "
        "or merge it into the existing three-class model."
    )


if __name__ == "__main__":
    main()
