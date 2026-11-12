"""Validation-only ablation of SOUL's privacy-redaction placeholders.

This diagnostic compares:
1. The existing saved multilingual model on the untouched validation text.
2. The same fixed model recipe retrained on training text after removing only
   SOUL's six explicit redaction placeholders, then evaluated on similarly
   stripped validation text.

It reads train and validation only. It never reads the initial holdout test,
does not change the saved baseline model, and does not save the ablation model.

Run from repository root:
    python data/ablate_multilingual_mask_markers.py
"""

import json
import re
from pathlib import Path

import joblib

from train_multilingual_baseline import (
    ARTIFACT_DIRECTORY,
    MODEL_PATH,
    SPLIT_DIRECTORY,
    build_pipeline,
    calculate_language_metrics,
    calculate_metrics,
    read_split,
    sha256_file,
)


MASK_MARKER_PATTERN = re.compile(
    r"\[(?:URL|DOMAIN|EMAIL_OR_UPI|PAN_LIKE|12_DIGIT_NUMBER|LONG_NUMBER)\]",
    flags=re.IGNORECASE,
)
ABLATION_REPORT_PATH = ARTIFACT_DIRECTORY / "multilingual_mask_marker_ablation.json"


def strip_mask_markers(text):
    """Remove only exact SOUL redaction placeholders, preserving other wording."""
    without_markers = MASK_MARKER_PATTERN.sub(" ", text or "")
    return " ".join(without_markers.split())


def evaluate_model(model, rows):
    """Return aggregate and language metrics for a supplied fixed set of rows."""
    texts = [row["text"] for row in rows]
    labels = [row["label"] for row in rows]
    predictions = model.predict(texts)
    return {
        "metrics": calculate_metrics(labels, predictions),
        "metrics_by_language": calculate_language_metrics(rows, predictions),
        "predictions": [str(value) for value in predictions],
    }


def build_ablation_report(train_rows, validation_rows, original_model):
    """Compare original and placeholder-stripped models on validation only."""
    if not train_rows or not validation_rows:
        raise ValueError("Train and validation rows must both be non-empty.")

    train_texts = [row["text"] for row in train_rows]
    train_labels = [row["label"] for row in train_rows]
    validation_texts = [row["text"] for row in validation_rows]
    validation_labels = [row["label"] for row in validation_rows]

    original_predictions = original_model.predict(validation_texts)
    original_metrics = calculate_metrics(validation_labels, original_predictions)
    original_by_language = calculate_language_metrics(
        validation_rows,
        original_predictions,
    )

    stripped_train_texts = [strip_mask_markers(text) for text in train_texts]
    stripped_validation_texts = [
        strip_mask_markers(text) for text in validation_texts
    ]

    if any(not text for text in stripped_train_texts + stripped_validation_texts):
        raise ValueError("Marker removal produced an empty message.")

    stripped_model = build_pipeline()
    stripped_model.fit(stripped_train_texts, train_labels)

    stripped_predictions = stripped_model.predict(stripped_validation_texts)
    stripped_metrics = calculate_metrics(
        validation_labels,
        stripped_predictions,
    )
    stripped_rows = [
        {**row, "text": stripped_text}
        for row, stripped_text in zip(validation_rows, stripped_validation_texts)
    ]
    stripped_by_language = calculate_language_metrics(
        stripped_rows,
        stripped_predictions,
    )

    metric_names = (
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
    )
    deltas = {
        name: round(
            stripped_metrics[name] - original_metrics[name],
            6,
        )
        for name in metric_names
    }

    language_comparison = {}
    languages = sorted(
        set(original_by_language) | set(stripped_by_language)
    )
    for language in languages:
        original = original_by_language[language]
        stripped = stripped_by_language[language]
        language_comparison[language] = {
            "rows": original["rows"],
            "label_support": original["label_support"],
            "original_accuracy": original["metrics"]["accuracy"],
            "without_markers_accuracy": stripped["metrics"]["accuracy"],
            "accuracy_delta": round(
                stripped["metrics"]["accuracy"]
                - original["metrics"]["accuracy"],
                6,
            ),
            "original_scam_recall": original["metrics"]["class_metrics"]["scam"]["recall"],
            "without_markers_scam_recall": stripped["metrics"]["class_metrics"]["scam"]["recall"],
            "scam_recall_delta": round(
                stripped["metrics"]["class_metrics"]["scam"]["recall"]
                - original["metrics"]["class_metrics"]["scam"]["recall"],
                6,
            ),
            "low_support": stripped["low_support"],
        }

    return {
        "experiment": "validation_only_privacy_marker_ablation",
        "train_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "test_partition_read": False,
        "original_model_retrained": False,
        "original_model_artifact_modified": False,
        "ablation_model_saved": False,
        "preprocessing_change": (
            "Remove only [URL], [DOMAIN], [EMAIL_OR_UPI], [PAN_LIKE], "
            "[12_DIGIT_NUMBER], [LONG_NUMBER] placeholders from text."
        ),
        "original_model_validation_metrics": original_metrics,
        "without_marker_model_validation_metrics": stripped_metrics,
        "aggregate_metric_delta_without_markers_minus_original": deltas,
        "language_comparison": language_comparison,
        "interpretation_limits": [
            "This is a validation-set diagnostic, not a new independent evaluation.",
            "The ablation retrains only on the existing train partition.",
            "The test partition is not read or used.",
            "Marker removal can alter token context as well as remove marker identity.",
            "A metric change estimates the contribution of these placeholders under this recipe; it does not prove causality.",
            "This synthetic dataset may still contain near-duplicate templates after marker removal.",
        ],
    }


def main():
    if not MODEL_PATH.is_file():
        raise SystemExit(
            f"Original model artifact not found: {MODEL_PATH}. "
            "Run data/train_multilingual_baseline.py first."
        )

    try:
        train_path = SPLIT_DIRECTORY / "train.csv"
        validation_path = SPLIT_DIRECTORY / "validation.csv"
        train_rows = read_split(train_path)
        validation_rows = read_split(validation_path)
        original_model = joblib.load(MODEL_PATH)

        report = build_ablation_report(
            train_rows,
            validation_rows,
            original_model,
        )
        report["split_sha256"] = {
            "train": sha256_file(train_path),
            "validation": sha256_file(validation_path),
        }
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Mask-marker ablation failed: {error}") from error

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with ABLATION_REPORT_PATH.open("w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)

    original = report["original_model_validation_metrics"]
    stripped = report["without_marker_model_validation_metrics"]
    deltas = report["aggregate_metric_delta_without_markers_minus_original"]

    print("SOUL — multilingual privacy-marker ablation")
    print("Training rows:", report["train_rows"])
    print("Validation rows:", report["validation_rows"])
    print("Test partition read: no")
    print("Original model retrained: no")
    print("Original model artifact modified: no")
    print("Ablation model saved: no")

    print("\nVALIDATION COMPARISON")
    print("METRIC               ORIGINAL   WITHOUT MARKERS   DELTA")
    for name in ("accuracy", "balanced_accuracy", "macro_f1", "weighted_f1"):
        print(
            f"{name:<20} "
            f"{original[name]:>8.4f} "
            f"{stripped[name]:>16.4f} "
            f"{deltas[name]:>+8.4f}"
        )

    print("\nPER-LANGUAGE ACCURACY / SCAM RECALL")
    print("LANGUAGE      ACC_ORIG  ACC_NO_MARK  SCAM_R_ORIG  SCAM_R_NO_MARK")
    for language, values in report["language_comparison"].items():
        print(
            f"{language:<12} "
            f"{values['original_accuracy']:>8.4f} "
            f"{values['without_markers_accuracy']:>12.4f} "
            f"{values['original_scam_recall']:>12.4f} "
            f"{values['without_markers_scam_recall']:>14.4f}"
            + ("  LOW SUPPORT" if values["low_support"] else "")
        )

    print("\nAggregate report saved locally:", ABLATION_REPORT_PATH)
    print(
        "\nInterpretation: this estimates validation performance change from "
        "removing explicit masking placeholders. It is not causal proof and "
        "does not establish real-world generalisation."
    )


if __name__ == "__main__":
    main()
