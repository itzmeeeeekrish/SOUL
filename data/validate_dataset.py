"""Validate the synthetic SOUL SMS Dataset v2 using Python's standard library."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

DATA_FILE = Path(__file__).parent / "synthetic" / "sms_messages_v2.csv"

REQUIRED_COLUMNS = [
    "message_id",
    "text",
    "label",
    "language",
    "scenario",
    "campaign_group",
    "split",
    "origin",
    "annotation_note",
]
ALLOWED_LABELS = {"legitimate", "spam", "scam"}
ALLOWED_LANGUAGES = {"en", "hi", "hinglish", "other"}
ALLOWED_SPLITS = {"train", "validation", "test"}
EXPECTED_LABEL_COUNTS = {"legitimate": 28, "spam": 28, "scam": 28}
EXPECTED_SPLIT_COUNTS = {
    "train": {"legitimate": 20, "spam": 20, "scam": 20},
    "validation": {"legitimate": 4, "spam": 4, "scam": 4},
    "test": {"legitimate": 4, "spam": 4, "scam": 4},
}
EXPECTED_GROUPS_PER_SPLIT = {"train": 15, "validation": 3, "test": 3}


def main():
    """Check schema, labels, counts and campaign-safe split assignments."""
    errors = []

    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            print("Dataset validation failed: CSV header is missing.")
            return 1

        missing = [name for name in REQUIRED_COLUMNS if name not in reader.fieldnames]
        if missing:
            print("Dataset validation failed: missing columns:", missing)
            return 1

        rows = list(reader)

    if not rows:
        print("Dataset validation failed: CSV has no rows.")
        return 1

    ids = set()
    label_counts = Counter()
    split_counts = defaultdict(Counter)
    groups = defaultdict(list)

    for line_number, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            if not row.get(column, "").strip():
                errors.append("Row {}: '{}' is empty.".format(line_number, column))

        message_id = row.get("message_id", "").strip()
        if message_id in ids:
            errors.append("Row {}: duplicate message_id '{}'.".format(line_number, message_id))
        ids.add(message_id)

        label = row.get("label", "").strip()
        split = row.get("split", "").strip()
        language = row.get("language", "").strip()
        group = row.get("campaign_group", "").strip()

        if label not in ALLOWED_LABELS:
            errors.append("Row {}: unsupported label '{}'.".format(line_number, label))
        else:
            label_counts[label] += 1

        if split not in ALLOWED_SPLITS:
            errors.append("Row {}: unsupported split '{}'.".format(line_number, split))
        elif label in ALLOWED_LABELS:
            split_counts[split][label] += 1

        if language not in ALLOWED_LANGUAGES:
            errors.append("Row {}: unsupported language '{}'.".format(line_number, language))

        if row.get("origin", "").strip() != "synthetic":
            errors.append("Row {}: v2 origin must be 'synthetic'.".format(line_number))

        groups[group].append(row)

    if len(rows) != 84:
        errors.append("Expected 84 rows; found {}.".format(len(rows)))

    if dict(label_counts) != EXPECTED_LABEL_COUNTS:
        errors.append(
            "Expected label counts {}; found {}.".format(
                EXPECTED_LABEL_COUNTS, dict(label_counts)
            )
        )

    for split, expected in EXPECTED_SPLIT_COUNTS.items():
        actual = dict(split_counts[split])
        if actual != expected:
            errors.append(
                "Split '{}' expected {}; found {}.".format(split, expected, actual)
            )

    if len(groups) != 21:
        errors.append("Expected 21 campaign groups; found {}.".format(len(groups)))

    group_counts = Counter()
    for group_name, group_rows in groups.items():
        if not group_name:
            errors.append("A campaign_group value is empty.")
            continue

        if len(group_rows) != 4:
            errors.append(
                "Campaign '{}' must have 4 variants; found {}.".format(
                    group_name, len(group_rows)
                )
            )

        labels = {row.get("label", "").strip() for row in group_rows}
        splits = {row.get("split", "").strip() for row in group_rows}

        if len(labels) != 1:
            errors.append("Campaign '{}' contains multiple labels.".format(group_name))
        if len(splits) != 1:
            errors.append("Campaign '{}' crosses multiple splits.".format(group_name))

        if len(splits) == 1:
            split_name = next(iter(splits))
            if split_name in ALLOWED_SPLITS:
                group_counts[split_name] += 1

    if dict(group_counts) != EXPECTED_GROUPS_PER_SPLIT:
        errors.append(
            "Expected campaign group counts {}; found {}.".format(
                EXPECTED_GROUPS_PER_SPLIT, dict(group_counts)
            )
        )

    if errors:
        print("Dataset validation failed:")
        for error in errors:
            print("-", error)
        return 1

    print("Dataset v2 validation passed.")
    print("Rows:", len(rows))
    for label in sorted(EXPECTED_LABEL_COUNTS):
        print("{}: {}".format(label, label_counts[label]))
    for split_name in ("train", "validation", "test"):
        row_total = sum(split_counts[split_name].values())
        print(
            "{}: {} rows across {} campaign groups".format(
                split_name, row_total, group_counts[split_name]
            )
        )
    print("Campaign leakage check: passed (no group crosses splits).")
    print("Note: synthetic data validates pipeline logic, not real-world model accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
