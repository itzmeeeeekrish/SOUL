"""Group flagged SMS into unique masked templates for a smaller local review.

This is a privacy-review helper only. It does not change or delete the source
dataset and does not decide whether a message is legitimate, spam or scam.

Groups are formed from normalised MASKED text. Different source messages can
therefore share a template if their detected identifiers are replaced by the
same placeholders. This is useful for reviewing repeated patterns, but it is
not a substitute for exact-message deduplication in the ML dataset.

The output stays under data/private/ (Git-ignored). Masking is not guaranteed
anonymisation; never upload or share the output.

Run from the repository root:
    python data/build_privacy_review_queue.py
"""

import csv
import io
import zipfile
from collections import Counter
from pathlib import Path

from audit_mendeley_privacy import (
    ARCHIVE_PATH,
    PATTERN_NAMES,
    detect_patterns,
    find_nested_member,
)
from create_masked_privacy_review import (
    mask_candidates,
    neutralize_spreadsheet_formula,
)


OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "private"
    / "mendeley_privacy_review_unique_templates.csv"
)


def normalise_template(masked_text: str) -> str:
    """Create a comparison key without changing the text saved for review."""
    return " ".join(masked_text.casefold().split())


def collect_review_groups(rows):
    """Group candidate rows by normalised masked text, retaining aggregate data."""
    groups = {}

    for row in rows:
        message = (row.get("TEXT") or "").strip()
        if not message:
            continue

        label = (row.get("LABEL") or "").strip().casefold() or "<blank>"
        flags = detect_patterns(message)
        matched_patterns = {
            name for name in PATTERN_NAMES if flags.get(name, False)
        }

        if not matched_patterns:
            continue

        masked_text = mask_candidates(message)
        key = normalise_template(masked_text)

        if key not in groups:
            groups[key] = {
                "masked_text": masked_text,
                "source_occurrences": 0,
                "source_label_counts": Counter(),
                "candidate_patterns": set(),
            }

        group = groups[key]
        group["source_occurrences"] += 1
        group["source_label_counts"][label] += 1
        group["candidate_patterns"].update(matched_patterns)

    return list(groups.values())


def read_source_rows(archive_path: Path):
    """Yield rows from the CSV nested inside the downloaded archive."""
    with zipfile.ZipFile(archive_path) as outer:
        nested_name = find_nested_member(outer, "Dataset_5971.zip")
        nested_bytes = outer.read(nested_name)

    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as inner:
        csv_name = find_nested_member(inner, "Dataset_5971.csv")

        with inner.open(csv_name) as raw_csv:
            text_stream = io.TextIOWrapper(
                raw_csv,
                encoding="utf-8-sig",
                newline="",
            )
            reader = csv.DictReader(text_stream)

            required = {"LABEL", "TEXT"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    "CSV is missing required columns: "
                    + ", ".join(sorted(missing))
                )

            for row in reader:
                yield row


def write_review_queue(groups, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as output:
        fieldnames = [
            "template_group_id",
            "source_occurrences",
            "source_labels",
            "source_label_counts",
            "source_label_conflict",
            "candidate_patterns",
            "masked_text",
            "manual_review_category",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for index, group in enumerate(groups, start=1):
            label_counts = group["source_label_counts"]
            labels = sorted(label_counts)
            label_conflict = len(labels) > 1

            writer.writerow(
                {
                    "template_group_id": f"PT{index:05d}",
                    "source_occurrences": group["source_occurrences"],
                    "source_labels": ";".join(labels),
                    "source_label_counts": ";".join(
                        f"{label}={label_counts[label]}" for label in labels
                    ),
                    "source_label_conflict": "yes" if label_conflict else "no",
                    "candidate_patterns": ";".join(
                        name
                        for name in PATTERN_NAMES
                        if name in group["candidate_patterns"]
                    ),
                    "masked_text": neutralize_spreadsheet_formula(
                        group["masked_text"]
                    ),
                    "manual_review_category": "",
                }
            )


def main() -> None:
    if not ARCHIVE_PATH.is_file():
        raise SystemExit(
            "Archive not found. Expected file:\n"
            f"{ARCHIVE_PATH}"
        )

    try:
        source_rows = list(read_source_rows(ARCHIVE_PATH))
        groups = collect_review_groups(source_rows)
        write_review_queue(groups, OUTPUT_PATH)
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
        raise SystemExit(
            f"Privacy review queue could not be built: {error}"
        ) from error

    flagged_rows = sum(group["source_occurrences"] for group in groups)
    collapsed_occurrences = flagged_rows - len(groups)
    label_conflict_groups = sum(
        len(group["source_label_counts"]) > 1 for group in groups
    )
    label_counts = Counter()
    for group in groups:
        for label, count in group["source_label_counts"].items():
            label_counts[label] += count

    print("SOUL — grouped local privacy review queue")
    print("Source rows read:", len(source_rows))
    print("Rows with candidate patterns:", flagged_rows)
    print("Unique masked templates:", len(groups))
    print("Repeated occurrences grouped:", collapsed_occurrences)
    print("Groups with multiple source labels:", label_conflict_groups)

    print("\nCandidate rows by source label:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count}")

    print("\nOutput:", OUTPUT_PATH)
    print(
        "\nReview one masked template at a time, not every source occurrence. "
        "A group with source_label_conflict=yes needs separate label review. "
        "This grouping is only for privacy review; do not use it as the ML "
        "train/test deduplication method."
    )
    print(
        "The output may still contain identifying context missed by regex. "
        "It stays local under data/private/ (Git-ignored); do not upload, "
        "commit or paste its contents into chat."
    )


if __name__ == "__main__":
    main()
