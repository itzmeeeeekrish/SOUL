"""Validate the synthetic SOUL SMS starter dataset using Python's standard library."""

import csv
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).parent / "synthetic" / "sms_messages.csv"

REQUIRED_COLUMNS = [
    "message_id",
    "text",
    "label",
    "language",
    "scenario",
    "campaign_group",
    "origin",
    "annotation_note",
]

ALLOWED_LABELS = {"legitimate", "spam", "scam"}
ALLOWED_LANGUAGES = {"en", "hi", "hinglish", "other"}
EXPECTED_LABEL_COUNTS = {"legitimate": 8, "spam": 8, "scam": 8}


def main():
    """Check required columns, row values, IDs and starter class counts."""
    errors = []

    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            print("Dataset validation failed: CSV header is missing.")
            return 1

        missing_columns = [
            column for column in REQUIRED_COLUMNS if column not in reader.fieldnames
        ]

        if missing_columns:
            print("Dataset validation failed: missing columns:", missing_columns)
            return 1

        rows = list(reader)

    if not rows:
        print("Dataset validation failed: CSV has no data rows.")
        return 1

    seen_ids = set()
    label_counts = Counter()

    for row_number, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row.get(column, "").strip():
                errors.append(
                    "Row {}: '{}' is empty.".format(row_number, column)
                )

        message_id = row.get("message_id", "").strip()

        if message_id in seen_ids:
            errors.append(
                "Row {}: duplicate message_id '{}'.".format(row_number, message_id)
            )
        seen_ids.add(message_id)

        label = row.get("label", "").strip()
        if label not in ALLOWED_LABELS:
            errors.append(
                "Row {}: unsupported label '{}'.".format(row_number, label)
            )
        else:
            label_counts[label] += 1

        language = row.get("language", "").strip()
        if language not in ALLOWED_LANGUAGES:
            errors.append(
                "Row {}: unsupported language '{}'.".format(row_number, language)
            )

        if row.get("origin", "").strip() != "synthetic":
            errors.append(
                "Row {}: starter dataset origin must be 'synthetic'.".format(row_number)
            )

    if dict(label_counts) != EXPECTED_LABEL_COUNTS:
        errors.append(
            "Unexpected class counts. Expected {}, found {}.".format(
                EXPECTED_LABEL_COUNTS, dict(label_counts)
            )
        )

    if errors:
        print("Dataset validation failed:")
        for error in errors:
            print("-", error)
        return 1

    print("Dataset validation passed.")
    print("Rows:", len(rows))
    for label in sorted(EXPECTED_LABEL_COUNTS):
        print("{}: {}".format(label, label_counts[label]))

    print("Note: this small synthetic dataset validates the format, not model accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
