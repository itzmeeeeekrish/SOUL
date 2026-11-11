"""Build a blinded, local label-review queue for baseline validation errors.

Run from the repository root:
    python data/build_validation_label_review_queue.py

Inputs are all local under data/private/:
- mendeley_prepared.csv
- mendeley_splits/validation.csv
- model_artifacts/baseline_metrics.json
- model_artifacts/validation_misclassified.csv

The blinded queue deliberately hides source labels, baseline labels and model
predictions. The separate key contains those fields but no message text.
Neither output is suitable for committing or public sharing.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from create_masked_privacy_review import neutralize_spreadsheet_formula
from train_text_baseline import (
    ARTIFACT_DIRECTORY,
    LABEL_ORDER,
    METRICS_PATH,
    SPLIT_DIRECTORY,
    sha256_file,
)


DATA_DIRECTORY = Path(__file__).resolve().parent
PREPARED_PATH = DATA_DIRECTORY / "private" / "mendeley_prepared.csv"
ERRORS_PATH = ARTIFACT_DIRECTORY / "validation_misclassified.csv"
BLIND_QUEUE_PATH = ARTIFACT_DIRECTORY / "validation_label_review_blind.csv"
REVIEW_KEY_PATH = ARTIFACT_DIRECTORY / "validation_label_review_key.csv"

SOURCE_LABEL_MAP = {
    "ham": "legitimate",
    "smishing": "scam",
    "spam": "spam",
}


def normalise_text(text):
    return " ".join((text or "").casefold().split())


def read_csv_rows(path, required_columns):
    if not path.is_file():
        raise FileNotFoundError(f"Required local file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = set(required_columns) - columns
        if missing:
            raise ValueError(
                f"{path.name} is missing columns: "
                + ", ".join(sorted(missing))
            )
        return list(reader)


def build_review_records(error_rows, validation_rows, prepared_rows):
    """Build blind review rows and a separate label/prediction key."""
    prepared_by_text = defaultdict(list)
    for row in prepared_rows:
        key = normalise_text(row.get("text"))
        if not key:
            raise ValueError("Prepared data contains blank text.")
        prepared_by_text[key].append(row)

    blind_rows = []
    key_rows = []
    used_review_ids = set()
    used_validation_rows = set()

    for error in error_rows:
        try:
            validation_row_number = int(error.get("validation_row", ""))
        except (TypeError, ValueError):
            raise ValueError("An error row has an invalid validation_row value.")

        if validation_row_number < 2:
            raise ValueError("Validation row numbers must start at CSV row 2.")
        if validation_row_number in used_validation_rows:
            raise ValueError("Duplicate validation_row in the error report.")
        used_validation_rows.add(validation_row_number)

        validation_index = validation_row_number - 2
        if validation_index >= len(validation_rows):
            raise ValueError("An error row points outside validation.csv.")

        validation = validation_rows[validation_index]
        if (validation.get("split") or "").strip().casefold() != "validation":
            raise ValueError("The referenced row is not in the validation split.")

        message = (validation.get("text") or "").strip()
        message_key = normalise_text(message)
        if not message:
            raise ValueError("Validation data contains blank text.")

        if normalise_text(error.get("text")) != message_key:
            raise ValueError("Error report text does not match validation.csv.")

        baseline_label = (validation.get("label") or "").strip().casefold()
        reported_actual = (error.get("actual_label") or "").strip().casefold()
        if baseline_label != reported_actual:
            raise ValueError("Error report actual label does not match validation.csv.")
        if baseline_label not in LABEL_ORDER:
            raise ValueError("Validation row has an unsupported baseline label.")

        model_prediction = (error.get("predicted_label") or "").strip().casefold()
        if model_prediction not in LABEL_ORDER or model_prediction == baseline_label:
            raise ValueError("Error report row is not a valid misclassification.")

        review_id = (validation.get("record_id") or "").strip()
        if not review_id:
            raise ValueError("Validation row is missing its record_id.")
        if review_id in used_review_ids:
            raise ValueError("Duplicate review_id in the validation split.")
        used_review_ids.add(review_id)

        source_records = prepared_by_text.get(message_key, [])
        if not source_records:
            raise ValueError("Could not match a validation message to prepared data.")

        source_labels = {
            (row.get("source_label") or "").strip().casefold()
            for row in source_records
        }
        if len(source_labels) != 1:
            raise ValueError(
                "A validation message maps to multiple source labels; "
                "manual provenance review is required."
            )

        source_label = next(iter(source_labels))
        if source_label not in SOURCE_LABEL_MAP:
            raise ValueError("Prepared data contains an unsupported source label.")
        if SOURCE_LABEL_MAP[source_label] != baseline_label:
            raise ValueError(
                "Source label does not match the frozen provisional baseline label."
            )

        try:
            source_occurrences = sum(
                int(row.get("source_occurrences", ""))
                for row in source_records
            )
        except (TypeError, ValueError):
            raise ValueError("Prepared data contains invalid source occurrence counts.")

        if source_occurrences < 1:
            raise ValueError("Source occurrence count must be positive.")

        # Blind sheet: no source label, baseline label, or model prediction.
        blind_rows.append(
            {
                "review_id": review_id,
                "text": neutralize_spreadsheet_formula(message),
                "soul_label": "",
                "review_status": "pending",
                "annotation_note": "",
            }
        )

        # Separate key: labels and scores, but no message text.
        try:
            score = float(error.get("top_class_probability", ""))
        except (TypeError, ValueError):
            raise ValueError("Error row has an invalid top-class score.")
        if not 0.0 <= score <= 1.0:
            raise ValueError("Top-class score must be between 0 and 1.")

        key_rows.append(
            {
                "review_id": review_id,
                "source_label": source_label,
                "baseline_label": baseline_label,
                "model_prediction": model_prediction,
                "top_class_probability": round(score, 4),
                "source_occurrences": source_occurrences,
            }
        )

    if not blind_rows:
        raise ValueError("No validation errors were available for review.")

    return blind_rows, key_rows


def write_csv(path, rows, columns):
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    validation_path = SPLIT_DIRECTORY / "validation.csv"

    try:
        with METRICS_PATH.open("r", encoding="utf-8") as source:
            metadata = json.load(source)
        saved_hash = metadata.get("split_sha256", {}).get("validation")
        if not saved_hash or saved_hash != sha256_file(validation_path):
            raise ValueError(
                "validation.csv does not match the saved baseline split hash."
            )

        validation_rows = read_csv_rows(
            validation_path,
            {"record_id", "label", "text", "split"},
        )
        error_rows = read_csv_rows(
            ERRORS_PATH,
            {
                "validation_row",
                "actual_label",
                "predicted_label",
                "top_class_probability",
                "text",
            },
        )
        prepared_rows = read_csv_rows(
            PREPARED_PATH,
            {
                "source_label",
                "label",
                "text",
                "source_occurrences",
                "soul_label",
                "review_status",
                "annotation_note",
            },
        )

        blind_rows, key_rows = build_review_records(
            error_rows,
            validation_rows,
            prepared_rows,
        )
    except (OSError, UnicodeError, csv.Error, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Review queue generation failed: {error}") from error

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    write_csv(
        BLIND_QUEUE_PATH,
        blind_rows,
        [
            "review_id",
            "text",
            "soul_label",
            "review_status",
            "annotation_note",
        ],
    )
    write_csv(
        REVIEW_KEY_PATH,
        key_rows,
        [
            "review_id",
            "source_label",
            "baseline_label",
            "model_prediction",
            "top_class_probability",
            "source_occurrences",
        ],
    )

    print("SOUL — blinded validation label-review queue")
    print("Review examples:", len(blind_rows))
    print("Blind queue hides source labels and model predictions: yes")
    print("Separate key contains labels/scores but no message text: yes")
    print("Validation split fingerprint verified: yes")
    print("\nLocal files:")
    print("  Blind review queue:", BLIND_QUEUE_PATH)
    print("  Separate review key:", REVIEW_KEY_PATH)
    print(
        "\nPrivacy: Both files stay in Git-ignored data/private/. Review the "
        "blind queue first. Do not open the key until independent labels "
        "have been entered. Never upload, commit or share message text."
    )


if __name__ == "__main__":
    main()
