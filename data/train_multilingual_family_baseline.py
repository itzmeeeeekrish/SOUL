"""Train/evaluate a family-separated multilingual development baseline.

Run after create_multilingual_family_splits.py:
    python data/train_multilingual_family_baseline.py --threshold 0.95
    python data/train_multilingual_family_baseline.py --threshold 0.98

Only the new family split's train and validation files are read. No test split
is opened, and no model is persisted or connected to the live SOUL API.
"""

import argparse
import json
from pathlib import Path

from train_multilingual_baseline import (
    ARTIFACT_DIRECTORY,
    LABEL_ORDER,
    build_pipeline,
    calculate_language_metrics,
    calculate_metrics,
    print_metrics,
    read_split,
    sha256_file,
)


DATA_DIRECTORY = Path(__file__).resolve().parent
FAMILY_SPLIT_ROOT = (
    DATA_DIRECTORY
    / "private"
    / "multilingual_candidates"
    / "family_splits"
)
ALLOWED_THRESHOLDS = (0.95, 0.98)


def validate_family_splits(train_rows, validation_rows):
    if not train_rows or not validation_rows:
        raise ValueError("Family train and validation splits must both be non-empty.")

    for name, rows in (("train", train_rows), ("validation", validation_rows)):
        labels = {row["label"] for row in rows}
        if labels != set(LABEL_ORDER):
            raise ValueError(f"{name} split must contain both ham and scam.")

    train_groups = {row["group_id"] for row in train_rows}
    validation_groups = {row["group_id"] for row in validation_rows}
    if train_groups & validation_groups:
        raise ValueError("A similarity family crosses train and validation.")

    train_hashes = {row["model_text_sha256"] for row in train_rows}
    validation_hashes = {
        row["model_text_sha256"] for row in validation_rows
    }
    if train_hashes & validation_hashes:
        raise ValueError("Exact model text crosses train and validation.")


def run_experiment(threshold):
    if threshold not in ALLOWED_THRESHOLDS:
        raise ValueError("Unsupported similarity threshold.")

    directory = FAMILY_SPLIT_ROOT / f"threshold_{int(threshold * 100):03d}"
    train_path = directory / "train.csv"
    validation_path = directory / "validation.csv"
    summary_path = directory / "split_summary.json"

    train_rows = read_split(train_path)
    validation_rows = read_split(validation_path)
    validate_family_splits(train_rows, validation_rows)

    pipeline = build_pipeline()
    pipeline.fit(
        [row["text"] for row in train_rows],
        [row["label"] for row in train_rows],
    )

    validation_predictions = pipeline.predict(
        [row["text"] for row in validation_rows]
    )
    validation_metrics = calculate_metrics(
        [row["label"] for row in validation_rows],
        validation_predictions,
    )
    language_metrics = calculate_language_metrics(
        validation_rows,
        validation_predictions,
    )

    if not summary_path.is_file():
        raise FileNotFoundError(
            f"Family split summary missing: {summary_path}. "
            "Create the family split first."
        )
    import json as json_module

    with summary_path.open("r", encoding="utf-8") as source:
        split_summary = json_module.load(source)

    report = {
        "experiment": "similarity_family_separated_multilingual_development_baseline",
        "source_type": "synthetic",
        "task": "binary scam_vs_ham",
        "similarity_threshold": threshold,
        "model": "character n-gram TF-IDF + Logistic Regression",
        "model_input": "message_text_only",
        "language_metadata_usage": "evaluation_only_not_a_model_feature",
        "training_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "test_partition_read": False,
        "model_artifact_saved": False,
        "live_detector_modified": False,
        "split_sha256": {
            "train": sha256_file(train_path),
            "validation": sha256_file(validation_path),
        },
        "family_split_summary": split_summary,
        "validation_metrics": validation_metrics,
        "validation_metrics_by_language": language_metrics,
        "limitations": [
            "This is a synthetic binary ham/scam development experiment.",
            "Only the original train and validation partitions were pooled; the original initial holdout test was not read.",
            "The old validation partition has appeared in prior diagnostics, so this is not an untouched independent final evaluation.",
            "Similarity-connected components are approximate template-family candidates, not verified campaign identities.",
            "Language-specific metrics with fewer than 20 examples in either class are preliminary.",
            "This model is not merged into SOUL's three-class detector.",
        ],
    }

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    report_path = (
        ARTIFACT_DIRECTORY
        / f"multilingual_family_baseline_threshold_{int(threshold * 100):03d}.json"
    )
    with report_path.open("w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)

    print("SOUL — similarity-family-separated development baseline")
    print("Threshold:", f"{threshold:.2f}")
    print("Training rows:", len(train_rows))
    print("Validation rows:", len(validation_rows))
    print("Original test partition read: no")
    print("Model artifact saved: no")
    print("Live detector modified: no")
    print_metrics(
        "family-separated validation",
        validation_metrics,
        language_metrics,
    )
    print("\nAggregate report saved locally:", report_path)
    print(
        "\nImportant: development-only synthetic result. It is not an "
        "independent final test or real-world fraud-detection accuracy."
    )
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Train and evaluate without opening the original test split."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        choices=ALLOWED_THRESHOLDS,
        default=0.95,
    )
    args = parser.parse_args()

    try:
        run_experiment(args.threshold)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Family baseline failed: {error}") from error


if __name__ == "__main__":
    main()
