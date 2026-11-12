"""Audit script/lexical coverage of the local prepared SMS dataset.

The script prints aggregate counts only. It never prints message text, record
IDs, source labels or model predictions.

Run from the repository root:
    python data/audit_language_coverage.py
"""

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIRECTORY = ROOT / "backend"
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.services.language_guard import inspect_language_support  # noqa: E402

INPUT_PATH = ROOT / "data" / "private" / "mendeley_prepared.csv"


def audit_language_rows(rows):
    counts = Counter()
    total = 0

    for row in rows:
        total += 1
        assessment = inspect_language_support(row.get("text", ""))
        if assessment["script_profile"] == "latin":
            if assessment["baseline_eligible"]:
                counts["latin_without_hinglish_markers"] += 1
            else:
                counts["romanized_hindi_signal"] += 1
        elif assessment["script_profile"] == "mixed_latin_non_latin":
            counts["mixed_script"] += 1
        else:
            counts["non_latin_script"] += 1

    return total, counts


def main():
    if not INPUT_PATH.is_file():
        raise SystemExit(
            f"Prepared dataset not found: {INPUT_PATH}. "
            "Run data/prepare_mendeley_dataset.py first."
        )

    try:
        with INPUT_PATH.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if "text" not in (reader.fieldnames or []):
                raise ValueError("Prepared dataset is missing the text column.")
            total, counts = audit_language_rows(reader)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(f"Language coverage audit failed: {error}") from error

    print("SOUL — language/script coverage audit")
    print("Prepared messages:", total)
    print("Latin script, no Romanized-Hindi markers:", counts["latin_without_hinglish_markers"])
    print("Romanized-Hindi lexical signals:", counts["romanized_hindi_signal"])
    print("Mixed Latin/non-Latin script:", counts["mixed_script"])
    print("Non-Latin script:", counts["non_latin_script"])
    print(
        "\nCaution: these are conservative script/lexicon indicators, not "
        "ground-truth language identification. Latin text may be English, "
        "Hinglish without a detected marker, or another language. Counts do "
        "not prove language coverage or model performance."
    )


if __name__ == "__main__":
    main()
