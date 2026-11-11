"""Aggregate-only privacy pattern audit for the Mendeley 2022 SMS archive.

Reads the nested CSV directly from the downloaded ZIP. It does not extract files,
write message contents, or print matched values.
Run from any directory with:
    python data/audit_mendeley_privacy.py
"""

import csv
import io
import re
import zipfile
from pathlib import Path


ARCHIVE_PATH = (
    Path(__file__).resolve().parent
    / "raw"
    / "mendeley_2022"
    / "SMS PHISHING DATASET FOR MACHINE LEARNING AND PATTERN RECOGNITION.zip"
)

NESTED_ZIP_SUFFIX = "Dataset_5971.zip"
CSV_SUFFIX = "Dataset_5971.csv"

# These patterns deliberately identify candidates, not confirmed personal data.
EMAIL_OR_UPI_PATTERN = re.compile(
    r"(?i)(?<![\w.+-])[a-z0-9.!#$%&'*+/=?^_{|}~-]+"
    r"@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+"
)

URL_PATTERN = re.compile(
    r"""(?i)\b(?:https?://|www\.)[^\s<>()\[\]{}"']+"""
)

# Also flag common bare domains that do not begin with http(s):// or www.
BARE_DOMAIN_PATTERN = re.compile(
    r"(?i)\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|org|net|edu|gov|in|co|io|app|info|biz|me|site|online|xyz|"
    r"top|live|store|tech|ai|uk|us|de|au|ca)\b"
)

# Broad number pattern: it can also match dates, IDs or account-like values.
# Therefore the report calls these "phone/long-number candidates".
PHONE_OR_LONG_NUMBER_PATTERN = re.compile(
    r"(?<!\w)\+?\d(?:[\s().-]*\d){6,14}(?!\w)"
)

TWELVE_DIGIT_PATTERN = re.compile(r"(?<!\d)(?:\d[\s-]?){11}\d(?!\d)")

# Indian PAN-like shape only; a pattern match is not proof of a valid PAN.
PAN_LIKE_PATTERN = re.compile(
    r"(?i)(?<![A-Z0-9])[A-Z]{5}\d{4}[A-Z](?![A-Z0-9])"
)


def find_nested_member(archive: zipfile.ZipFile, suffix: str) -> str:
    matches = [
        name for name in archive.namelist()
        if name.endswith("/" + suffix) or name == suffix
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one archive member ending in {suffix!r}; "
            f"found {len(matches)}."
        )
    return matches[0]


def audit_archive(archive_path: Path) -> dict:
    counts = {
        "total_rows": 0,
        "blank_text_rows": 0,
        "email_or_upi_like_rows": 0,
        "url_or_domain_like_rows": 0,
        "phone_or_long_number_candidate_rows": 0,
        "twelve_digit_candidate_rows": 0,
        "pan_like_candidate_rows": 0,
        "rows_with_any_candidate_pattern": 0,
    }

    with zipfile.ZipFile(archive_path) as outer:
        nested_name = find_nested_member(outer, NESTED_ZIP_SUFFIX)
        nested_bytes = outer.read(nested_name)

    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as inner:
        csv_name = find_nested_member(inner, CSV_SUFFIX)

        with inner.open(csv_name) as raw_csv:
            text_stream = io.TextIOWrapper(
                raw_csv,
                encoding="utf-8-sig",
                newline="",
            )
            reader = csv.DictReader(text_stream)

            required_columns = {"LABEL", "TEXT", "URL", "EMAIL", "PHONE"}
            actual_columns = set(reader.fieldnames or [])
            missing = required_columns - actual_columns
            if missing:
                raise ValueError(
                    "CSV is missing required columns: "
                    + ", ".join(sorted(missing))
                )

            for row in reader:
                counts["total_rows"] += 1
                message = (row.get("TEXT") or "").strip()

                if not message:
                    counts["blank_text_rows"] += 1
                    continue

                email_match = bool(EMAIL_OR_UPI_PATTERN.search(message))
                url_match = bool(
                    URL_PATTERN.search(message)
                    or BARE_DOMAIN_PATTERN.search(message)
                )
                phone_match = bool(
                    PHONE_OR_LONG_NUMBER_PATTERN.search(message)
                )
                twelve_digit_match = bool(
                    TWELVE_DIGIT_PATTERN.search(message)
                )
                pan_match = bool(PAN_LIKE_PATTERN.search(message))

                counts["email_or_upi_like_rows"] += email_match
                counts["url_or_domain_like_rows"] += url_match
                counts["phone_or_long_number_candidate_rows"] += phone_match
                counts["twelve_digit_candidate_rows"] += twelve_digit_match
                counts["pan_like_candidate_rows"] += pan_match

                counts["rows_with_any_candidate_pattern"] += any(
                    (
                        email_match,
                        url_match,
                        phone_match,
                        twelve_digit_match,
                        pan_match,
                    )
                )

    return counts


def main() -> None:
    if not ARCHIVE_PATH.is_file():
        raise SystemExit(
            "Archive not found. Expected file:\n"
            f"{ARCHIVE_PATH}"
        )

    try:
        results = audit_archive(ARCHIVE_PATH)
    except (zipfile.BadZipFile, OSError, UnicodeError, ValueError) as error:
        raise SystemExit(f"Privacy audit could not complete: {error}") from error

    print("SOUL — Mendeley SMS privacy pattern audit")
    print("Source rows:", results["total_rows"])
    print("Blank TEXT rows:", results["blank_text_rows"])
    print("\nRows with possible sensitive-data patterns:")
    print("  Email/UPI-like:", results["email_or_upi_like_rows"])
    print("  URL/domain-like:", results["url_or_domain_like_rows"])
    print(
        "  Phone/long-number candidates:",
        results["phone_or_long_number_candidate_rows"],
    )
    print("  12-digit numeric candidates:", results["twelve_digit_candidate_rows"])
    print("  PAN-like candidates:", results["pan_like_candidate_rows"])
    print(
        "  Rows with at least one candidate pattern:",
        results["rows_with_any_candidate_pattern"],
    )
    print(
        "\nNote: Counts are broad pattern matches, not proof of personal data. "
        "No message text or matched value was printed or saved."
    )


if __name__ == "__main__":
    main()
