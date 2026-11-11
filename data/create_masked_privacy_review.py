"""Create a LOCAL masked review CSV for candidate SMS rows.

The output is written under data/private/, which is ignored by Git.
The masked file may still contain identifying context that regex does not detect.
It is intended for controlled local review only.

Run from the repository root:
    python data/create_masked_privacy_review.py
"""

import csv
import io
import zipfile
from collections import Counter
from pathlib import Path

from audit_mendeley_privacy import (
    ARCHIVE_PATH,
    BARE_DOMAIN_PATTERN,
    EMAIL_OR_UPI_PATTERN,
    PAN_LIKE_PATTERN,
    PHONE_OR_LONG_NUMBER_PATTERN,
    TWELVE_DIGIT_PATTERN,
    URL_PATTERN,
    detect_patterns,
    find_nested_member,
)

OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "private"
    / "mendeley_privacy_review_masked.csv"
)


def mask_candidates(message: str) -> str:
    """Mask regex candidates while preserving surrounding message context."""
    masked = URL_PATTERN.sub("[URL]", message)
    masked = BARE_DOMAIN_PATTERN.sub("[DOMAIN]", masked)
    masked = EMAIL_OR_UPI_PATTERN.sub("[EMAIL_OR_UPI]", masked)
    masked = PAN_LIKE_PATTERN.sub("[PAN_LIKE]", masked)
    masked = TWELVE_DIGIT_PATTERN.sub("[12_DIGIT_NUMBER]", masked)
    masked = PHONE_OR_LONG_NUMBER_PATTERN.sub("[LONG_NUMBER]", masked)
    return masked


def neutralize_spreadsheet_formula(text: str) -> str:
    """Prevent a masked SMS from being interpreted as a spreadsheet formula."""
    stripped = text.lstrip(" \t\r\n")
    if stripped.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def create_review_file() -> tuple[int, Counter]:
    if not ARCHIVE_PATH.is_file():
        raise FileNotFoundError(f"Source archive not found: {ARCHIVE_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows_written = 0
    label_counts = Counter()

    with zipfile.ZipFile(ARCHIVE_PATH) as outer:
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

            with OUTPUT_PATH.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as output:
                writer = csv.DictWriter(
                    output,
                    fieldnames=[
                        "source_row",
                        "label",
                        "candidate_patterns",
                        "masked_text",
                        "manual_review_category",
                    ],
                )
                writer.writeheader()

                for source_row, row in enumerate(reader, start=1):
                    message = (row.get("TEXT") or "").strip()
                    label = (row.get("LABEL") or "").strip().casefold()

                    if not message:
                        continue

                    flags = detect_patterns(message)
                    matched = [name for name, found in flags.items() if found]

                    if not matched:
                        continue

                    safe_masked_text = neutralize_spreadsheet_formula(
                        mask_candidates(message)
                    )

                    writer.writerow(
                        {
                            "source_row": source_row,
                            "label": label,
                            "candidate_patterns": ";".join(matched),
                            "masked_text": safe_masked_text,
                            "manual_review_category": "",
                        }
                    )
                    rows_written += 1
                    label_counts[label or "<blank>"] += 1

    return rows_written, label_counts


def main() -> None:
    try:
        rows_written, label_counts = create_review_file()
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
        raise SystemExit(
            f"Masked review file could not be created: {error}"
        ) from error

    print("SOUL — local masked privacy review")
    print("Candidate rows written:", rows_written)
    print("Rows by source label:")
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count}")
    print("\nOutput:", OUTPUT_PATH)
    print(
        "\nIMPORTANT: The file contains masked message context, not guaranteed "
        "anonymous data. It stays local under data/private/ (Git-ignored). "
        "The masked_text field is also protected against common spreadsheet "
        "formula injection prefixes. Do not upload it, commit it, or paste "
        "its contents into chat."
    )


if __name__ == "__main__":
    main()
