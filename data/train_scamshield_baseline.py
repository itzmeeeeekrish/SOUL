"""Train a separate ScamShield three-class character n-gram baseline.

Reads the locally curated, group-safe ScamShield train/validation/test files.
Only message text is a model feature. Labels are provisional silver labels.
Language and source provenance are evaluation metadata only.

Run from repository root:
    python data/train_scamshield_baseline.py

The fixed first baseline evaluates validation and the initial holdout test once.
Do not tune the model using test results. Keep this experiment separate from
SOUL's live detector and the historical Mendeley benchmark.
"""

import argparse
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
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline


DATA_DIRECTORY = Path(__file__).resolve().parent
SPLIT_DIRECTORY = (
    DATA_DIRECTORY / "private" / "scamshield_candidate" / "splits"
)
ARTIFACT_DIRECTORY = DATA_DIRECTORY / "private" / "model_artifacts"
MODEL_PATH = (
    ARTIFACT_DIRECTORY / "scamshield_three_class_char_tfidf_logistic.joblib"
)
METRICS_PATH = ARTIFACT_DIRECTORY / "scamshield_three_class_baseline_metrics.json"

LABEL_ORDER = ("legitimate", "spam", "scam")
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


def normalise_text(value):
    return " ".join(str(value or "").casefold().split())


def sha256_text(value):
    return hashlib.sha256(normalise_text(value).encode("utf-8")).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_json_list(value, field_name):
    try:
        result = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON in {field_name}: {error}") from error
    if not isinstance(result, list) or not result:
        raise ValueError(f"{field_name} must be a non-empty JSON list.")
    if any(not isinstance(item, str) or not item.strip() for item in result):
        raise ValueError(f"{field_name} must contain non-empty strings.")
    return sorted(set(item.strip() for item in result))


def read_split(path):
    """Read and validate one private split without using metadata as features."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"ScamShield split not found: {path}. "
            "Run data/split_scamshield_candidate.py first."
        )

    required = {
        "model_row_id",
        "text",
        "label",
        "label_provenance",
        "masked_text_sha256",
        "languages_json",
        "source_datasets_json",
    }
    expected_split = path.stem.casefold()
    rows = []
    seen_ids = set()

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path.name} is missing columns: "
                + ", ".join(sorted(missing))
            )

        for row_number, row in enumerate(reader, start=2):
            row_id = str(row["model_row_id"] or "").strip()
            text = str(row["text"] or "").strip()
            label = str(row["label"] or "").strip().casefold()
            text_hash = str(row["masked_text_sha256"] or "").strip()

            if not row_id or not text or not text_hash:
                raise ValueError(
                    f"{path.name} has a blank ID, text or hash at row "
                    f"{row_number}."
                )
            if row_id in seen_ids:
                raise ValueError(
                    f"{path.name} contains duplicate model_row_id {row_id}."
                )
            seen_ids.add(row_id)

            if label not in LABEL_ORDER:
                raise ValueError(
                    f"{path.name} has unsupported label {label!r} "
                    f"at row {row_number}."
                )
            if sha256_text(text) != text_hash:
                raise ValueError(
                    f"{path.name} masked text hash mismatch at row "
                    f"{row_number}."
                )

            languages = parse_json_list(
                row["languages_json"], "languages_json"
            )
            if len(languages) != 1:
                raise ValueError(
                    f"{path.name} row {row_id} has conflicting language tags."
                )
            sources = parse_json_list(
                row["source_datasets_json"], "source_datasets_json"
            )

            row["_language"] = languages[0].casefold()
            row["_sources"] = sources
            rows.append(row)

    if not rows:
        raise ValueError(f"{path.name} contains no rows.")
    return rows


def validate_splits(splits):
    """Require all classes and no exact masked-text/ID leakage."""
    seen_ids = {}
    seen_hashes = {}

    for split_name in SPLIT_NAMES:
        rows = splits.get(split_name)
        if not rows:
            raise ValueError(f"The {split_name} split is missing or empty.")

        labels = {row["label"] for row in rows}
        if labels != set(LABEL_ORDER):
            raise ValueError(
                f"The {split_name} split must contain all three classes."
            )

        for row in rows:
            row_id = row["model_row_id"]
            text_hash = row["masked_text_sha256"]

            if row_id in seen_ids:
                raise ValueError(
                    f"Record ID {row_id} appears in {seen_ids[row_id]} "
                    f"and {split_name}."
                )
            if text_hash in seen_hashes:
                raise ValueError(
                    "Exact masked text appears in "
                    f"{seen_hashes[text_hash]} and {split_name}."
                )
            seen_ids[row_id] = split_name
            seen_hashes[text_hash] = split_name


def build_pipeline():
    """Fixed lightweight multilingual baseline: character TF-IDF + Logistic Regression."""
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
    if not y_true or len(y_true) != len(y_pred):
        raise ValueError("True and predicted label counts must match and be non-empty.")

    precision, recall, f1_values, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(LABEL_ORDER),
        zero_division=0,
    )
    matrix = confusion_matrix(
        y_true, y_pred, labels=list(LABEL_ORDER)
    )
    total = int(matrix.sum())
    class_metrics = {}

    for index, label in enumerate(LABEL_ORDER):
        true_positive = int(matrix[index, index])
        false_positive = int(matrix[:, index].sum() - true_positive)
        false_negative = int(matrix[index, :].sum() - true_positive)
        true_negative = total - true_positive - false_positive - false_negative
        denominator = false_positive + true_negative
        class_metrics[label] = {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1_values[index]),
            "support": int(support[index]),
            "false_positive_rate": (
                float(false_positive / denominator) if denominator else 0.0
            ),
        }

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(
            f1_score(
                y_true, y_pred, labels=list(LABEL_ORDER),
                average="macro", zero_division=0,
            )
        ),
        "weighted_f1": float(
            f1_score(
                y_true, y_pred, labels=list(LABEL_ORDER),
                average="weighted", zero_division=0,
            )
        ),
        "class_metrics": class_metrics,
        "confusion_matrix": matrix.astype(int).tolist(),
        "confusion_matrix_labels": list(LABEL_ORDER),
    }


def group_metrics(rows, predictions, metadata_key):
    if len(rows) != len(predictions):
        raise ValueError("Rows and prediction counts do not match.")

    grouped = defaultdict(lambda: {"true": [], "predicted": []})
    for row, prediction in zip(rows, predictions):
        values = (
            [row[metadata_key]]
            if metadata_key == "_language"
            else row[metadata_key]
        )
        for value in values:
            grouped[value]["true"].append(row["label"])
            grouped[value]["predicted"].append(prediction)

    results = {}
    for group_name in sorted(grouped):
        y_true = grouped[group_name]["true"]
        y_pred = grouped[group_name]["predicted"]
        support = Counter(y_true)
        metrics = calculate_metrics(y_true, y_pred)
        low_support = [
            label for label in LABEL_ORDER
            if support.get(label, 0) < MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION
        ]
        results[group_name] = {
            "rows": len(y_true),
            "class_support": {
                label: int(support.get(label, 0)) for label in LABEL_ORDER
            },
            "metrics": metrics,
            "low_support": bool(low_support),
            "support_note": (
                "Preliminary: fewer than "
                f"{MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION} examples for "
                + ", ".join(low_support)
                if low_support else
                f"At least {MINIMUM_CLASS_SUPPORT_FOR_INTERPRETATION} examples per class."
            ),
        }
    return results


def count_labels(rows):
    counts = Counter(row["label"] for row in rows)
    return {label: int(counts.get(label, 0)) for label in LABEL_ORDER}


def print_metrics(split_name, metrics, language_metrics, source_metrics):
    print(f"\n{split_name.upper()} OVERALL")
    print(f"  Accuracy:          {metrics['accuracy']:.4f}")
    print(f"  Balanced accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"  Macro F1:          {metrics['macro_f1']:.4f}")
    print(f"  Weighted F1:       {metrics['weighted_f1']:.4f}")

    print("\n  Per-class metrics:")
    print("  CLASS       PRECISION  RECALL   F1       FPR      SUPPORT")
    for label in LABEL_ORDER:
        value = metrics["class_metrics"][label]
        print(
            f"  {label:<11} "
            f"{value['precision']:>9.4f} "
            f"{value['recall']:>8.4f} "
            f"{value['f1']:>8.4f} "
            f"{value['false_positive_rate']:>8.4f} "
            f"{value['support']:>9}"
        )

    print("\n  Per-language macro F1 / class support:")
    for language, value in language_metrics.items():
        print(
            f"  {language:<12} macro-F1={value['metrics']['macro_f1']:.4f} "
            f"support={value['class_support']} "
            f"{'PRELIMINARY' if value['low_support'] else ''}"
        )

    print("\n  Per-source macro F1 / class support (overlapping provenance views):")
    for source, value in source_metrics.items():
        print(
            f"  {source:<40} macro-F1={value['metrics']['macro_f1']:.4f} "
            f"support={value['class_support']} "
            f"{'PRELIMINARY' if value['low_support'] else ''}"
        )


def run_experiment(split_directory=SPLIT_DIRECTORY,
                   artifact_directory=ARTIFACT_DIRECTORY,
                   validation_only=False):
    split_directory = Path(split_directory)
    artifact_directory = Path(artifact_directory)
    split_paths = {
        name: split_directory / f"scamshield_{name}.csv"
        for name in SPLIT_NAMES
    }

    splits = {
        "train": read_split(split_paths["train"]),
        "validation": read_split(split_paths["validation"]),
    }
    if not validation_only:
        splits["test"] = read_split(split_paths["test"])
    validate_splits(splits)

    train_rows = splits["train"]
    pipeline = build_pipeline()
    pipeline.fit(
        [row["text"] for row in train_rows],
        [row["label"] for row in train_rows],
    )

    validation_rows = splits["validation"]
    validation_predictions = pipeline.predict(
        [row["text"] for row in validation_rows]
    )
    validation_metrics = calculate_metrics(
        [row["label"] for row in validation_rows],
        validation_predictions,
    )
    validation_language = group_metrics(
        validation_rows, validation_predictions, "_language"
    )
    validation_source = group_metrics(
        validation_rows, validation_predictions, "_sources"
    )

    report = {
        "experiment": "scamshield_three_class_development_baseline",
        "source_dataset": "sidzzz07/scamshield-dataset",
        "task": "three_class_legitimate_spam_scam",
        "model": "character n-gram TF-IDF + Logistic Regression",
        "model_input": "message_text_only",
        "language_metadata_usage": "evaluation_only_not_a_model_feature",
        "source_metadata_usage": "evaluation_only_not_a_model_feature",
        "training_labels": "provisional_silver_not_human_verified",
        "human_verified_ground_truth": False,
        "model_config": {
            "vectorizer": VECTORIZER_CONFIG,
            "classifier": CLASSIFIER_CONFIG,
        },
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "split_sha256": {
            name: sha256_file(path)
            for name, path in split_paths.items()
            if name in splits
        },
        "split_sizes": {
            name: len(rows) for name, rows in splits.items()
        },
        "class_counts": {
            name: count_labels(rows) for name, rows in splits.items()
        },
        "validation_metrics": validation_metrics,
        "validation_metrics_by_language": validation_language,
        "validation_metrics_by_source": validation_source,
        "test_evaluated": False,
        "model_artifact_saved": False,
        "live_detector_modified": False,
        "limitations": [
            "Source labels are provisional silver labels, not independent human-verified ground truth.",
            "The split is a mixed-source random holdout, not source-disjoint or independent external evaluation.",
            "The source corpus is heavily imbalanced by source; Smishing_Dataset dominates the input.",
            "Exact masked-text separation does not guarantee campaign/template-family separation.",
            "Regex masking is not proof of complete anonymisation.",
            "Source-level metrics are overlapping provenance views when a deduplicated message has multiple source occurrences.",
            "This experiment does not alter SOUL's live detector or the historical Mendeley benchmark.",
        ],
    }

    if not validation_only:
        test_rows = splits["test"]
        test_predictions = pipeline.predict([row["text"] for row in test_rows])
        test_metrics = calculate_metrics(
            [row["label"] for row in test_rows], test_predictions
        )
        test_language = group_metrics(test_rows, test_predictions, "_language")
        test_source = group_metrics(test_rows, test_predictions, "_sources")
        report.update({
            "test_metrics": test_metrics,
            "test_metrics_by_language": test_language,
            "test_metrics_by_source": test_source,
            "test_evaluated": True,
            "test_set_policy": (
                "Initial fixed-recipe holdout evaluation. Do not tune model "
                "features, hyperparameters or thresholds using these results."
            ),
        })

    artifact_directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH if artifact_directory == ARTIFACT_DIRECTORY
                else artifact_directory / MODEL_PATH.name, compress=3)
    report["model_artifact_saved"] = True
    metrics_path = (
        METRICS_PATH if artifact_directory == ARTIFACT_DIRECTORY
        else artifact_directory / METRICS_PATH.name
    )
    metrics_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("SOUL — ScamShield three-class baseline")
    print("Task: legitimate / spam / scam")
    print("Model input: message text only")
    print("Language and source: evaluation metadata only")
    print("Training rows:", len(train_rows))
    print("Train class counts:", count_labels(train_rows))
    print("Validation rows:", len(validation_rows))
    print("Test rows:", len(splits["test"]) if "test" in splits else "not opened")
    print("Scikit-learn:", sklearn.__version__)
    print("Python:", platform.python_version())

    print_metrics(
        "validation", validation_metrics, validation_language,
        validation_source,
    )
    if not validation_only:
        print_metrics("test (initial fixed holdout)", test_metrics,
                      test_language, test_source)

    vectorizer = pipeline.named_steps["tfidf"]
    model_path = (
        MODEL_PATH if artifact_directory == ARTIFACT_DIRECTORY
        else artifact_directory / MODEL_PATH.name
    )
    print("\nPrivate model artifacts saved:")
    print("  Character features:", len(vectorizer.vocabulary_))
    print("  Model:", model_path)
    print("  Metrics:", metrics_path)
    print("  Test evaluated:", "yes" if not validation_only else "no")
    print(
        "\nImportant: These are results against provisional silver labels "
        "on a mixed-source split, not real-world fraud-detection accuracy."
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validation-only",
        action="store_true",
        help="Do not open the test split; report validation metrics only.",
    )
    args = parser.parse_args()

    try:
        run_experiment(validation_only=args.validation_only)
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"ScamShield baseline failed: {error}") from error


if __name__ == "__main__":
    main()
