"""Prepare a local, deduplicated and redacted Mendeley SMS derivative.

This script:
- maps source labels to SOUL's three classes;
- quarantines exact normalised-text groups with conflicting source labels;
- collapses same-label exact duplicates into one prepared record;
- redacts broad candidate identifiers from message text;
- keeps candidate-presence indicators as metadata for later experiments;
- compares supplied YES/NO flags with SOUL's independently detected flags.

All outputs are written under data/private/ (Git-ignored). The output may still
contain personal context missed by regex. It is a local research derivative,
not an approved public dataset and not a claim of anonymisation.

Run from the repository root:
    python data/prepare_mendeley_dataset.py
"""

import csv
import io
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from audit_mendeley_privacy import (
    ARCHIVE_PATH,
    detect_patterns,
    find_nested_member,
)
from create_masked_privacy_review import (
    mask_candidates,
    neutralize_spreadsheet_formula,
)


OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "private"
PREPARED_PATH = OUTPUT_DIRECTORY / "mendeley_prepared.csv"
QUARANTINE_PATH = OUTPUT_DIRECTORY / "mendeley_quarantine.csv"

LABEL_MAP = {
    "ham": "legitimate",
    "smishing": "scam",
    "spam": "spam",
}


def normalise_text(text):
    """Case-fold and collapse whitespace for exact-duplicate comparison."""
    return " ".join((text or "").casefold().split())


def map_source_label(raw_label):
    """Map the three known source labels; return None for anything unexpected."""
    return LABEL_MAP.get((raw_label or "").strip().casefold())


def source_yes_no(value):
    """Convert the source's YES/NO flag to 1/0, or None if unrecognised."""
    normalised = (value or "").strip().casefold()
    if normalised == "yes":
        return 1
    if normalised == "no":
        return 0
    return None


def read_source_rows(archive_path):
    """Yield CSV records from the nested ZIP without extracting files."""
    with zipfile.ZipFile(archive_path) as outer:
        nested_name = find_nested_member(outer, "Dataset_5971.zip")
        nested_bytes = outer.read(nested_name)

    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as inner:
        csv_name = find_nested_member(inner, "Dataset_5971.csv")

        with inner.open(csv_name) as raw_csv:
            stream = io.TextIOWrapper(
                raw_csv,
                encoding="utf-8-sig",
                newline="",
            )
            reader = csv.DictReader(stream)

            required = {"LABEL", "TEXT", "URL", "EMAIL", "PHONE"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    "CSV is missing required columns: "
                    + ", ".join(sorted(missing))
                )

            for row in reader:
                yield row


def prepare_rows(rows):
    """Return prepared unique records, quarantined groups and aggregate stats."""
    groups = defaultdict(list)
    quarantine = []
    stats = Counter()

    for source_row_number, row in enumerate(rows, start=1):
        stats["source_rows"] += 1
        message = (row.get("TEXT") or "").strip()
        raw_label = (row.get("LABEL") or "").strip()
        mapped_label = map_source_label(raw_label)

        if not message:
            stats["blank_text_rows"] += 1
            quarantine.append(
                {
                    "reason": "blank_text",
                    "source_occurrences": 1,
                    "source_labels": raw_label.casefold(),
                    "label_counts": "",
                    "masked_text": "",
                }
            )
            continue

        if mapped_label is None:
            stats["unknown_label_rows"] += 1
            quarantine.append(
                {
                    "reason": "unknown_label",
                    "source_occurrences": 1,
                    "source_labels": raw_label.casefold() or "<blank>",
                    "label_counts": "",
                    "masked_text": neutralize_spreadsheet_formula(
                        mask_candidates(message)
                    ),
                }
            )
            continue

        key = normalise_text(message)
        groups[key].append(
            {
                "message": message,
                "source_label": raw_label.casefold(),
                "mapped_label": mapped_label,
                "source_url": source_yes_no(row.get("URL")),
                "source_email": source_yes_no(row.get("EMAIL")),
                "source_phone": source_yes_no(row.get("PHONE")),
            }
        )

    prepared = []
    for normalised_text, records in groups.items():
        labels = {record["mapped_label"] for record in records}
        label_counts = Counter(record["source_label"] for record in records)
        representative = records[0]["message"]
        masked_text = neutralize_spreadsheet_formula(
            mask_candidates(representative)
        )

        if len(labels) > 1:
            stats["conflict_groups"] += 1
            stats["conflict_rows"] += len(records)
            quarantine.append(
                {
                    "reason": "conflicting_labels_same_normalised_text",
                    "source_occurrences": len(records),
                    "source_labels": ";".join(sorted(label_counts)),
                    "label_counts": ";".join(
                        f"{label}={label_counts[label]}"
                        for label in sorted(label_counts)
                    ),
                    "masked_text": masked_text,
                }
            )
            continue

        if len(records) > 1:
            stats["same_label_duplicate_groups"] += 1
            stats["duplicate_rows_collapsed"] += len(records) - 1

        features = detect_patterns(representative)
        recomputed_flags = {
            "url": int(features["url_domain"]),
            "email": int(features["email_upi"]),
            "phone": int(features["phone_long_number"]),
        }

        for record in records:
            record_source_flags = {
                "url": record["source_url"],
                "email": record["source_email"],
                "phone": record["source_phone"],
            }
            for name, source_value in record_source_flags.items():
                if (
                    source_value is not None
                    and source_value != recomputed_flags[name]
                ):
                    stats[f"{name}_flag_mismatches"] += 1

        prepared_source_flags = {}
        for name in ("url", "email", "phone"):
            distinct_values = {
                record[f"source_{name}"]
                for record in records
                if record[f"source_{name}"] is not None
            }
            if len(distinct_values) > 1:
                stats[f"{name}_flag_inconsistent_duplicate_groups"] += 1
                prepared_source_flags[name] = ""
            elif distinct_values:
                prepared_source_flags[name] = next(iter(distinct_values))
            else:
                prepared_source_flags[name] = ""

        prepared.append(
            {
                "record_id": f"M{len(prepared) + 1:05d}",
                "label": records[0]["mapped_label"],
                "text": masked_text,
                "source_occurrences": len(records),
                "has_url_candidate": int(features["url_domain"]),
                "has_email_upi_candidate": int(features["email_upi"]),
                "has_long_number_candidate": int(
                    features["phone_long_number"]
                ),
                "has_12_digit_candidate": int(features["twelve_digit"]),
                "has_pan_like_candidate": int(features["pan_like"]),
                "source_url_flag": prepared_source_flags["url"],
                "source_email_flag": prepared_source_flags["email"],
                "source_phone_flag": prepared_source_flags["phone"],
            }
        )

    stats["exact_text_groups"] = len(groups)
    stats["prepared_unique_records"] = len(prepared)
    stats["quarantine_groups"] = len(quarantine)
    stats["quarantine_rows"] = sum(
        item["source_occurrences"] for item in quarantine
    )
    stats["prepared_rows"] = sum(
        item["source_occurrences"] for item in prepared
    )

    return prepared, quarantine, stats


def write_outputs(prepared, quarantine):
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    prepared_columns = [
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
    ]
    quarantine_columns = [
        "reason",
        "source_occurrences",
        "source_labels",
        "label_counts",
        "masked_text",
    ]

    with PREPARED_PATH.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=prepared_columns)
        writer.writeheader()
        writer.writerows(prepared)

    with QUARANTINE_PATH.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=quarantine_columns)
        writer.writeheader()
        writer.writerows(quarantine)


def main():
    if not ARCHIVE_PATH.is_file():
        raise SystemExit(
            "Archive not found. Expected file:\n"
            f"{ARCHIVE_PATH}"
        )

    try:
        prepared, quarantine, stats = prepare_rows(
            read_source_rows(ARCHIVE_PATH)
        )
        write_outputs(prepared, quarantine)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Dataset preparation failed: {error}") from error

    label_counts = Counter(row["label"] for row in prepared)

    print("SOUL — local Mendeley dataset preparation")
    print("Source rows:", stats["source_rows"])
    print("Exact normalised-text groups:", stats["exact_text_groups"])
    print("Conflict groups quarantined:", stats["conflict_groups"])
    print("Rows in conflict groups:", stats["conflict_rows"])
    print("Same-label duplicate groups:", stats["same_label_duplicate_groups"])
    print("Duplicate rows collapsed:", stats["duplicate_rows_collapsed"])
    print("Prepared unique records:", stats["prepared_unique_records"])
    print("Quarantine groups:", stats["quarantine_groups"])
    print("Rows represented in quarantine:", stats["quarantine_rows"])

    print("\nPrepared class counts:")
    for label in ("legitimate", "scam", "spam"):
        print(f"  {label}: {label_counts[label]}")

    print("\nSource-flag vs SOUL-regex mismatches:")
    print("  URL:", stats["url_flag_mismatches"])
    print("  EMAIL:", stats["email_flag_mismatches"])
    print("  PHONE:", stats["phone_flag_mismatches"])
    print("  Duplicate groups with inconsistent source flags:")
    print("    URL:", stats["url_flag_inconsistent_duplicate_groups"])
    print("    EMAIL:", stats["email_flag_inconsistent_duplicate_groups"])
    print("    PHONE:", stats["phone_flag_inconsistent_duplicate_groups"])

    print("\nLocal output files:")
    print("  Prepared:", PREPARED_PATH)
    print("  Quarantine:", QUARANTINE_PATH)
    print(
        "\nIMPORTANT: Outputs stay under data/private/ (Git-ignored). "
        "Text is redacted using broad candidate patterns, but this is not "
        "guaranteed anonymisation. Do not upload, commit or paste these files. "
        "This script does not create train/validation/test splits or train a model."
    )


if __name__ == "__main__":
    main()
