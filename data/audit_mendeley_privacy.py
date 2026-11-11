"""Aggregate-only privacy pattern audit for the Mendeley 2022 SMS archive.

Reads the nested CSV directly from the downloaded ZIP. It does not extract files,
write message contents, or print matched values.
Run from the repository root:
    python data/audit_mendeley_privacy.py
"""

import csv
import io
import re
import zipfile
from collections import Counter, defaultdict
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

# Broad number pattern: it can also match dates, OTPs, IDs or references.
PHONE_OR_LONG_NUMBER_PATTERN = re.compile(
    r"(?<!\w)\+?\d(?:[\s().-]*\d){6,14}(?!\w)"
)

TWELVE_DIGIT_PATTERN = re.compile(r"(?<!\d)(?:\d[\s-]?){11}\d(?!\d)")

# Indian PAN-like shape only; a pattern match is not proof of a valid PAN.
PAN_LIKE_PATTERN = re.compile(
    r"(?i)(?<![A-Z0-9])[A-Z]{5}\d{4}[A-Z](?![A-Z0-9])"
)

PATTERN_NAMES = (
    "email_upi",
    "url_domain",
    "phone_long_number",
    "twelve_digit",
    "pan_like",
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


def detect_patterns(message: str) -> dict:
    """Return booleans only; never return or store the matched text."""
    return {
        "email_upi": bool(EMAIL_OR_UPI_PATTERN.search(message)),
        "url_domain": bool(
            URL_PATTERN.search(message)
            or BARE_DOMAIN_PATTERN.search(message)
        ),
        "phone_long_number": bool(
            PHONE_OR_LONG_NUMBER_PATTERN.search(message)
        ),
        "twelve_digit": bool(TWELVE_DIGIT_PATTERN.search(message)),
        "pan_like": bool(PAN_LIKE_PATTERN.search(message)),
    }


def audit_archive(archive_path: Path) -> dict:
    totals = Counter()
    by_label = defaultdict(Counter)
    combinations = Counter()

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
                totals["total_rows"] += 1
                message = (row.get("TEXT") or "").strip()
                label = (row.get("LABEL") or "").strip().casefold() or "<blank>"

                if not message:
                    totals["blank_text_rows"] += 1
                    by_label[label]["blank_text_rows"] += 1
                    combinations["blank_text"] += 1
                    continue

                flags = detect_patterns(message)
                matched = [name for name in PATTERN_NAMES if flags[name]]

                for name in matched:
                    totals[name] += 1
                    by_label[label][name] += 1

                if matched:
                    totals["rows_with_any_candidate_pattern"] += 1
                    by_label[label]["rows_with_any"] += 1
                    combinations[" + ".join(matched)] += 1
                else:
                    combinations["none"] += 1

                by_label[label]["rows"] += 1

    return {
        "totals": totals,
        "by_label": by_label,
        "combinations": combinations,
    }


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

    totals = results["totals"]

    print("SOUL — Mendeley SMS privacy pattern audit")
    print("Source rows:", totals["total_rows"])
    print("Blank TEXT rows:", totals["blank_text_rows"])
    print("\nRows with possible sensitive-data patterns:")
    print("  Email/UPI-like:", totals["email_upi"])
    print("  URL/domain-like:", totals["url_domain"])
    print("  Phone/long-number candidates:", totals["phone_long_number"])
    print("  12-digit numeric candidates:", totals["twelve_digit"])
    print("  PAN-like candidates:", totals["pan_like"])
    print(
        "  Rows with at least one candidate pattern:",
        totals["rows_with_any_candidate_pattern"],
    )

    print("\nPattern candidates by source label:")
    print(
        "  LABEL       ROWS  ANY  EMAIL/UPI  URL  PHONE/LONG  12-DIGIT  PAN"
    )
    for label in sorted(results["by_label"]):
        counts = results["by_label"][label]
        print(
            f"  {label:<10} "
            f"{counts['rows']:>5} "
            f"{counts['rows_with_any']:>4} "
            f"{counts['email_upi']:>10} "
            f"{counts['url_domain']:>4} "
            f"{counts['phone_long_number']:>10} "
            f"{counts['twelve_digit']:>9} "
            f"{counts['pan_like']:>4}"
        )

    print("\nCombination counts (one row may match multiple pattern types):")
    for combination, count in sorted(results["combinations"].items()):
        print(f"  {combination}: {count}")

    print(
        "\nNote: Counts are broad pattern matches, not proof of personal data. "
        "No message text or matched value was printed or saved."
    )


if __name__ == "__main__":
    main()
