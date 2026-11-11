"""Create a local, validation-only error report for SOUL's text baseline.

Run from the repository root:
    python data/analyze_baseline_errors.py

The report is based only on validation.csv. It does not read or evaluate
test.csv, and it does not retrain or modify the model.

The CSV contains message text and must stay local under Git-ignored
data/private/. Regex masking is not guaranteed anonymisation, so do not share
the CSV or paste message contents into public tools.
"""

import csv
import json
from pathlib import Path

import joblib
from sklearn.metrics import confusion_matrix

from train_text_baseline import (
    ARTIFACT_DIRECTORY,
    LABEL_ORDER,
    METRICS_PATH,
    MODEL_PATH,
    SPLIT_DIRECTORY,
    read_split,
    sha256_file,
)


SUMMARY_PATH = ARTIFACT_DIRECTORY / "validation_error_summary.json"
ERRORS_PATH = ARTIFACT_DIRECTORY / "validation_misclassified.csv"


def build_error_rows(rows, predictions, probabilities, class_labels):
    """Return only wrong predictions, with their model scores and source text."""
    if not (len(rows) == len(predictions) == len(probabilities)):
        raise ValueError("Rows, predictions and probabilities must have equal lengths.")

    class_labels = list(class_labels)
    if not class_labels:
        raise ValueError("The model must provide at least one class label.")

    errors = []

    for index, (row, predicted, scores) in enumerate(
        zip(rows, predictions, probabilities),
        start=2,
    ):
        if len(scores) != len(class_labels):
            raise ValueError("Probability columns do not match model classes.")

        actual = row["label"]
        predicted = str(predicted)

        if actual == predicted:
            continue

        top_index = max(range(len(scores)), key=lambda item: scores[item])
        errors.append(
            {
                "validation_row": index,
                "actual_label": actual,
                "predicted_label": predicted,
                "top_class": class_labels[top_index],
                "top_class_probability": round(float(scores[top_index]), 4),
                "text": row["text"],
            }
        )

    return errors


def build_error_summary(y_true, y_pred):
    """Return aggregate validation errors without including message text."""
    if len(y_true) != len(y_pred):
        raise ValueError("Actual and predicted labels must have equal lengths.")
    if not y_true:
        raise ValueError("Validation data must not be empty.")

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=list(LABEL_ORDER),
    )

    error_pairs = []
    for actual_index, actual_label in enumerate(LABEL_ORDER):
        for predicted_index, predicted_label in enumerate(LABEL_ORDER):
            if actual_index == predicted_index:
                continue

            count = int(matrix[actual_index, predicted_index])
            if count:
                error_pairs.append(
                    {
                        "actual": actual_label,
                        "predicted": predicted_label,
                        "count": count,
                    }
                )

    error_pairs.sort(key=lambda item: item["count"], reverse=True)

    total = len(y_true)
    correct = sum(
        1 for actual, predicted in zip(y_true, y_pred)
        if actual == predicted
    )

    return {
        "split": "validation_only",
        "total_rows": total,
        "correct_rows": correct,
        "misclassified_rows": total - correct,
        "accuracy": round(correct / total, 4),
        "confusion_matrix_labels": list(LABEL_ORDER),
        "confusion_matrix": matrix.astype(int).tolist(),
        "error_pairs": error_pairs,
        "probability_note": (
            "Top-class probabilities are model scores, not calibrated "
            "confidence or proof that a message is fraudulent."
        ),
        "test_set_policy": (
            "This report reads validation.csv only. The initial test set "
            "must not be used for error analysis or model tuning."
        ),
    }


def save_error_csv(path, errors):
    """Save message-level errors to a local CSV file."""
    fieldnames = [
        "validation_row",
        "actual_label",
        "predicted_label",
        "top_class",
        "top_class_probability",
        "text",
    ]

    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(errors)


def main():
    validation_path = SPLIT_DIRECTORY / "validation.csv"

    if not MODEL_PATH.is_file() or not METRICS_PATH.is_file():
        raise SystemExit(
            "Baseline model/metrics not found. Run python data\\train_text_baseline.py "
            "from the repository root first."
        )

    try:
        rows = read_split(validation_path)
        with METRICS_PATH.open("r", encoding="utf-8") as source:
            saved_metadata = json.load(source)
    except (OSError, UnicodeError, csv.Error, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Validation input/metadata error: {error}") from error

    saved_hash = (
        saved_metadata.get("split_sha256", {}).get("validation")
        if isinstance(saved_metadata, dict)
        else None
    )
    if not saved_hash or saved_hash != sha256_file(validation_path):
        raise SystemExit(
            "The current validation.csv does not match the split used for the "
            "saved baseline. Restore/regenerate the original split and retrain "
            "only as a separately documented experiment."
        )

    # Only load the model artifact generated by your own trusted local run.
    pipeline = joblib.load(MODEL_PATH)

    texts = [row["text"] for row in rows]
    y_true = [row["label"] for row in rows]
    y_pred = pipeline.predict(texts)
    probabilities = pipeline.predict_proba(texts)
    class_labels = pipeline.classes_

    errors = build_error_rows(
        rows,
        y_pred,
        probabilities,
        class_labels,
    )
    summary = build_error_summary(y_true, y_pred)

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with SUMMARY_PATH.open("w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2)

    save_error_csv(ERRORS_PATH, errors)

    print("SOUL — validation-only baseline error analysis")
    print("Validation rows:", summary["total_rows"])
    print("Correct predictions:", summary["correct_rows"])
    print("Misclassified rows:", summary["misclassified_rows"])
    print("Accuracy:", f"{summary['accuracy']:.4f}")

    print("\nMisclassification pairs (actual -> predicted):")
    if summary["error_pairs"]:
        for item in summary["error_pairs"]:
            print(
                f"  {item['actual']} -> {item['predicted']}: "
                f"{item['count']}"
            )
    else:
        print("  None")

    print("\nLocal reports saved:")
    print("  Aggregate summary:", SUMMARY_PATH)
    print("  Message-level errors:", ERRORS_PATH)
    print(
        "\nPrivacy note: The CSV contains message text. Keep it local; "
        "do not commit, upload or share its contents. Masking is not "
        "guaranteed anonymisation."
    )
    print(
        "Evaluation note: Top-class probabilities are not calibrated "
        "confidence. The test set was not read."
    )


if __name__ == "__main__":
    main()
