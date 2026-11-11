"""Validate the local prepared Mendeley derivative using aggregate counts only.

Reads data/private/mendeley_prepared.csv and never prints message text or IDs.
It checks schema, labels, blank records, metadata values, residual regex
candidates, exact masked-text collisions and class balance.

Run from the repository root:
    python data/validate_prepared_dataset.py
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

from audit_mendeley_privacy import detect_patterns


INPUT_PATH = (
    Path(__file__).resolve().parent
    / "private"
    / "mendeley_prepared.csv"
)

REQUIRED_COLUMNS = {
    "record_id",
    "label",
    "text",
    "source_occurrences",
    "has_url_candidate",
    "has_email_upi_candidate",
    "has_long_number_candidate",
    "has_12_digit_candidate",
    "has_pan_like_candidate",
    "source_url_flag",
    "source_email_flag",
    "source_phone_flag",
}
ALLOWED_LABELS = {"legitimate", "scam", "spam"}
BINARY_COLUMNS = {
    "has_url_candidate",
    "has_email_upi_candidate",
    "has_long_number_candidate",
    "has_12_digit_candidate",
    "has_pan_like_candidate",
    "source_url_flag",
    "source_email_flag",
    "source_phone_flag",
}


def normalise_text(text):
    return " ".join((text or "").casefold().split())


def audit_records(records):
    """Return aggregate validation counts without retaining or printing text."""
    stats = Counter()
    label_counts = Counter()
    record_ids = set()
    masked_groups = defaultdict(list)

    for row in records:
        stats["total_records"] += 1

        record_id = (row.get("record_id") or "").strip()
        if not record_id:
            stats["missing_record_ids"] += 1
        elif record_id in record_ids:
            stats["duplicate_record_id_rows"] += 1
        else:
            record_ids.add(record_id)

        label = (row.get("label") or "").strip().casefold()
        if label not in ALLOWED_LABELS:
            stats["invalid_label_rows"] += 1
        else:
            label_counts[label] += 1

        text = (row.get("text") or "").strip()
        if not text:
            stats["blank_text_rows"] += 1
            continue

        key = normalise_text(text)
        masked_groups[key].append(label)

        flags = detect_patterns(text)
        matched = [name for name, found in flags.items() if found]
        if matched:
            stats["residual_candidate_rows"] += 1
            for name in matched:
                stats[f"residual_{name}_rows"] += 1

        for column in BINARY_COLUMNS:
            value = (row.get(column) or "").strip()
            if value not in {"", "0", "1"}:
                stats["invalid_binary_metadata_values"] += 1

        try:
            occurrences = int(row.get("source_occurrences", ""))
            if occurrences < 1:
                stats["invalid_source_occurrence_values"] += 1
            else:
                stats["source_occurrences_total"] += occurrences
        except (TypeError, ValueError):
            stats["invalid_source_occurrence_values"] += 1

    for labels in masked_groups.values():
        if len(labels) > 1:
            stats["masked_text_collision_groups"] += 1
            stats["records_in_masked_text_collision_groups"] += len(labels)
            if len(set(labels)) > 1:
                stats["cross_label_masked_text_collision_groups"] += 1

    stats["unique_masked_texts"] = len(masked_groups)
    return stats, label_counts


def read_prepared_csv(path):
    if not path.is_file():
        raise FileNotFoundError(
            f"Prepared CSV not found: {path}\n"
            "Run data/prepare_mendeley_dataset.py first."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                "Prepared CSV is missing columns: "
                + ", ".join(sorted(missing))
            )
        return list(reader)


def main():
    try:
        records = read_prepared_csv(INPUT_PATH)
        stats, label_counts = audit_records(records)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(f"Prepared-data validation failed: {error}") from error

    print("SOUL — prepared dataset validation")
    print("Prepared records:", stats["total_records"])
    print("Unique record IDs:", stats["total_records"] - stats["missing_record_ids"] - stats["duplicate_record_id_rows"])
    print("Missing record IDs:", stats["missing_record_ids"])
    print("Duplicate record-ID rows:", stats["duplicate_record_id_rows"])
    print("Blank text rows:", stats["blank_text_rows"])
    print("Invalid label rows:", stats["invalid_label_rows"])
    print("Invalid binary metadata values:", stats["invalid_binary_metadata_values"])
    print("Invalid source occurrence values:", stats["invalid_source_occurrence_values"])
    print("Source occurrences represented:", stats["source_occurrences_total"])

    print("\nClass balance:")
    for label in ("legitimate", "scam", "spam"):
        count = label_counts[label]
        percentage = count / stats["total_records"] * 100 if stats["total_records"] else 0
        print(f"  {label}: {count} ({percentage:.1f}%)")

    print("\nResidual regex candidates in prepared text:")
    print("  Any candidate:", stats["residual_candidate_rows"])
    print("  Email/UPI-like:", stats["residual_email_upi_rows"])
    print("  URL/domain-like:", stats["residual_url_domain_rows"])
    print("  Phone/long-number:", stats["residual_phone_long_number_rows"])
    print("  12-digit:", stats["residual_twelve_digit_rows"])
    print("  PAN-like:", stats["residual_pan_like_rows"])

    print("\nCollisions after masking:")
    print("  Unique masked texts:", stats["unique_masked_texts"])
    print("  Repeated masked-text groups:", stats["masked_text_collision_groups"])
    print(
        "  Records in repeated masked-text groups:",
        stats["records_in_masked_text_collision_groups"],
    )
    print(
        "  Repeated masked-text groups with different labels:",
        stats["cross_label_masked_text_collision_groups"],
    )

    print(
        "\nNote: Regex checks only the patterns known to this project. Zero "
        "residual matches does not prove the text is anonymous. Masked-text "
        "collisions can arise because different original identifiers were "
        "replaced with the same placeholder. This validator does not split "
        "data or train a model."
    )


if __name__ == "__main__":
    main()
