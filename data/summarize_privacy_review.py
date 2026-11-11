"""Print aggregate counts from a locally reviewed masked privacy CSV.

Expected input:
    data/private/mendeley_privacy_review_masked.csv

Add a manual_review_category column in a spreadsheet editor and use one of
the allowed values below. This script prints counts only; it never prints
masked message text or row identifiers.

Run from the repository root:
    python data/summarize_privacy_review.py
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path


INPUT_PATH = (
    Path(__file__).resolve().parent
    / "private"
    / "mendeley_privacy_review_masked.csv"
)

ALLOWED_CATEGORIES = {
    "phone_or_contact",
    "email_or_upi",
    "website_link",
    "otp",
    "transaction_reference",
    "date_or_amount",
    "other_personal_data",
    "multiple_categories",
    "false_positive",
    "unclear",
}


def summarize_review(path: Path) -> tuple[int, int, Counter, dict]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Review CSV not found: {path}\n"
            "Run data/create_masked_privacy_review.py first."
        )

    total_rows = 0
    unclassified = 0
    invalid_categories = 0
    by_category = Counter()
    by_label = defaultdict(Counter)

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)

        required_columns = {
            "label",
            "candidate_patterns",
            "masked_text",
            "manual_review_category",
        }
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Review CSV needs a manual_review_category column. "
                "Open it locally, add that column, classify each row, and save "
                "as CSV UTF-8. Missing columns: "
                + ", ".join(sorted(missing))
            )

        for row in reader:
            total_rows += 1
            label = (row.get("label") or "").strip().casefold() or "<blank>"
            category = (
                row.get("manual_review_category") or ""
            ).strip().casefold()

            by_label[label]["rows"] += 1

            if not category:
                unclassified += 1
                by_label[label]["unclassified"] += 1
                continue

            if category not in ALLOWED_CATEGORIES:
                invalid_categories += 1
                by_label[label]["invalid"] += 1
                continue

            by_category[category] += 1
            by_label[label][category] += 1

    return total_rows, unclassified, invalid_categories, by_category, by_label


def main() -> None:
    try:
        total, unclassified, invalid, by_category, by_label = summarize_review(
            INPUT_PATH
        )
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(f"Privacy review summary could not complete: {error}") from error

    classified = total - unclassified - invalid

    print("SOUL — local privacy review summary")
    print("Candidate rows:", total)
    print("Classified rows:", classified)
    print("Unclassified rows:", unclassified)
    print("Rows with invalid category values:", invalid)

    print("\nManual review categories:")
    for category in sorted(ALLOWED_CATEGORIES):
        print(f"  {category}: {by_category[category]}")

    print("\nBreakdown by source label:")
    print("  LABEL       ROWS  CLASSIFIED  UNCLASSIFIED  INVALID")
    for label in sorted(by_label):
        counts = by_label[label]
        rows = counts["rows"]
        missing = counts["unclassified"]
        bad = counts["invalid"]
        done = rows - missing - bad
        print(f"  {label:<10} {rows:>5} {done:>11} {missing:>13} {bad:>8}")

    print(
        "\nNo message text, matched value or source row number was printed. "
        "This is a manual review summary, not a claim that the dataset is "
        "anonymous or safe to publish."
    )


if __name__ == "__main__":
    main()
