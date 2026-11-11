"""Train and evaluate SOUL's first text-only TF-IDF + Logistic Regression baseline.

Input files are created by data/create_mendeley_splits.py under data/private/.
Only the text column is used as X and label as y. The test partition is
evaluated once by this fixed recipe and must not be used for model tuning.

Run from the repository root:
    python data/train_text_baseline.py

Outputs stay under data/private/model_artifacts/ (Git-ignored):
    tfidf_logistic_regression.joblib
    baseline_metrics.json

Only load the locally generated joblib artifact if you trust its origin. Joblib
uses pickle-based serialization; loading an untrusted artifact can execute code.
"""

import csv
import hashlib
import json
import platform
from collections import Counter
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


SPLIT_DIRECTORY = (
    Path(__file__).resolve().parent
    / "private"
    / "mendeley_splits"
)
ARTIFACT_DIRECTORY = (
    Path(__file__).resolve().parent
    / "private"
    / "model_artifacts"
)
MODEL_PATH = ARTIFACT_DIRECTORY / "tfidf_logistic_regression.joblib"
METRICS_PATH = ARTIFACT_DIRECTORY / "baseline_metrics.json"

LABEL_ORDER = ("legitimate", "scam", "spam")
SPLIT_NAMES = ("train", "validation", "test")

VECTORIZER_CONFIG = {
    "ngram_range": [1, 2],
    "min_df": 2,
    "max_features": 50000,
    "sublinear_tf": True,
    "lowercase": True,
}
CLASSIFIER_CONFIG = {
    "class_weight": "balanced",
    "max_iter": 2000,
    "random_state": 42,
}


def normalise_text(text):
    """Normalise whitespace and case for leakage checks."""
    return " ".join((text or "").casefold().split())


def read_split(path):
    """Read only text and label; deliberately ignore audit metadata columns."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Split file not found: {path}\n"
            "Run data/create_mendeley_splits.py first."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"text", "label", "split"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path.name} is missing columns: " + ", ".join(sorted(missing))
            )

        rows = []
        expected_split = path.stem
        for row_number, row in enumerate(reader, start=2):
            text = (row.get("text") or "").strip()
            label = (row.get("label") or "").strip().casefold()
            split = (row.get("split") or "").strip().casefold()

            if not text:
                raise ValueError(f"{path.name} contains blank text at row {row_number}.")
            if label not in LABEL_ORDER:
                raise ValueError(
                    f"{path.name} contains an unsupported label at row {row_number}."
                )
            if split != expected_split:
                raise ValueError(
                    f"{path.name} contains a row assigned to {split!r}, "
                    f"not {expected_split!r}."
                )

            # The only features passed to the model are text and label.
            rows.append({"text": text, "label": label})

    if not rows:
        raise ValueError(f"{path.name} contains no data rows.")
    return rows


def validate_splits(splits):
    """Check all classes exist and no identical normalised text is repeated."""
    seen_texts = {}

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

        for row in splits[split_name]:
            key = normalise_text(row["text"])
            if key in seen_texts:
                previous_split = seen_texts[key]
                raise ValueError(
                    "Duplicate normalised model text detected in "
                    f"{previous_split!r} and {split_name!r}. "
                    "Regenerate and inspect the grouped split."
                )
            seen_texts[key] = split_name


def build_pipeline():
    """Build the fixed first baseline pipeline."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=50000,
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
    """Calculate aggregate and one-vs-rest metrics for each class."""
    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=list(LABEL_ORDER),
    )
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

        false_positive_rate = (
            false_positive / (false_positive + true_negative)
            if (false_positive + true_negative)
            else 0.0
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
        "macro_f1": float(f1_score(
            y_true,
            y_pred,
            labels=list(LABEL_ORDER),
            average="macro",
            zero_division=0,
        )),
        "weighted_f1": float(f1_score(
            y_true,
            y_pred,
            labels=list(LABEL_ORDER),
            average="weighted",
            zero_division=0,
        )),
        "class_metrics": class_metrics,
        "confusion_matrix": matrix.astype(int).tolist(),
        "confusion_matrix_labels": list(LABEL_ORDER),
    }


def sha256_file(path):
    """Return a file fingerprint for experiment traceability."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def print_metrics(split_name, metrics):
    print(f"\n{split_name.upper()} METRICS")
    print(f"  Accuracy:          {metrics['accuracy']:.4f}")
    print(f"  Balanced accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"  Macro F1:           {metrics['macro_f1']:.4f}")
    print(f"  Weighted F1:        {metrics['weighted_f1']:.4f}")

    print("\n  Per-class metrics (one-vs-rest FPR):")
    print("  CLASS        PRECISION  RECALL  F1      FPR     SUPPORT")
    for label in LABEL_ORDER:
        values = metrics["class_metrics"][label]
        print(
            f"  {label:<12} "
            f"{values['precision']:>9.4f} "
            f"{values['recall']:>7.4f} "
            f"{values['f1']:>7.4f} "
            f"{values['false_positive_rate']:>7.4f} "
            f"{values['support']:>8}"
        )

    print("\n  Confusion matrix (rows = actual, columns = predicted):")
    print("  actual / predicted:", "  ".join(LABEL_ORDER))
    for label, row in zip(LABEL_ORDER, metrics["confusion_matrix"]):
        print(f"  {label:<12}", "  ".join(str(value) for value in row))


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
        raise SystemExit(f"Baseline input validation failed: {error}") from error

    train_texts = [row["text"] for row in splits["train"]]
    train_labels = [row["label"] for row in splits["train"]]

    print("SOUL — TF-IDF + Logistic Regression baseline")
    print("Model input: text only")
    print("Target: label")
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

    # This is the first fixed-recipe holdout evaluation. Do not tune against it.
    test_true = [row["label"] for row in splits["test"]]
    test_texts = [row["text"] for row in splits["test"]]
    test_predictions = pipeline.predict(test_texts)
    test_metrics = calculate_metrics(test_true, test_predictions)

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH, compress=3)

    metadata = {
        "model": "TF-IDF + Logistic Regression",
        "model_input": "text_only",
        "target": "label",
        "labels": list(LABEL_ORDER),
        "random_state": 42,
        "vectorizer_config": VECTORIZER_CONFIG,
        "classifier_config": CLASSIFIER_CONFIG,
        "scikit_learn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "split_sha256": {
            name: sha256_file(path)
            for name, path in split_paths.items()
        },
        "split_sizes": {
            name: len(splits[name])
            for name in SPLIT_NAMES
        },
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "test_set_policy": (
            "Fixed initial evaluation only. Do not use test results to tune "
            "features, hyperparameters or thresholds."
        ),
    }

    with METRICS_PATH.open("w", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2)

    print_metrics("validation", validation_metrics)
    print_metrics("test (initial holdout)", test_metrics)

    vectorizer = pipeline.named_steps["tfidf"]
    print("\nModel artefacts saved locally:")
    print("  Vocabulary features:", len(vectorizer.vocabulary_))
    print("  Model:", MODEL_PATH)
    print("  Metrics:", METRICS_PATH)
    print(
        "\nImportant: This is a first exploratory baseline on a class-imbalanced "
        "dataset. Test results must not be used for tuning. Exact-text split "
        "does not guarantee campaign-independent evaluation. No real-world "
        "fraud-detection accuracy claim is justified by this experiment."
    )


if __name__ == "__main__":
    main()
