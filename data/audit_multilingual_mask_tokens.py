"""Audit how privacy-redaction placeholders are distributed by label.

This diagnostic reads only the multilingual train and validation partitions.
It does not read the initial holdout test, fit a model, or modify any artifact.

Run from the repository root:
    python data/audit_multilingual_mask_tokens.py

Only aggregate counts and percentages are printed and saved.
"""

import json
from collections import defaultdict
from pathlib import Path

from train_multilingual_baseline import (
    ARTIFACT_DIRECTORY,
    SPLIT_DIRECTORY,
    read_split,
)


REPORT_PATH = ARTIFACT_DIRECTORY / "multilingual_mask_token_audit.json"

MASK_MARKERS = {
    "url": "[URL]",
    "domain": "[DOMAIN]",
    "email_or_upi": "[EMAIL_OR_UPI]",
    "pan_like": "[PAN_LIKE]",
    "twelve_digit_number": "[12_DIGIT_NUMBER]",
    "long_number": "[LONG_NUMBER]",
}


def calculate_marker_rates(rows):
    """Count messages containing each marker overall and by source label."""
    if not rows:
        raise ValueError("Cannot audit an empty split.")

    labels = sorted({row["label"] for row in rows})
    result = {
        "rows": len(rows),
        "overall": {},
        "by_label": {},
    }

    for marker_name, marker in MASK_MARKERS.items():
        count = sum(marker.casefold() in row["text"].casefold() for row in rows)
        result["overall"][marker_name] = {
            "messages": int(count),
            "rate": round(count / len(rows), 4),
        }

    for label in labels:
        label_rows = [row for row in rows if row["label"] == label]
        marker_counts = {}
        for marker_name, marker in MASK_MARKERS.items():
            count = sum(
                marker.casefold() in row["text"].casefold()
                for row in label_rows
            )
            marker_counts[marker_name] = {
                "messages": int(count),
                "rate": round(count / len(label_rows), 4),
            }
        result["by_label"][label] = {
            "rows": len(label_rows),
            "markers": marker_counts,
        }

    return result


def calculate_language_label_marker_rates(rows):
    """Return compact marker rates grouped by language and label."""
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["language"], row["label"])].append(row)

    output = {}
    for (language, label), group_rows in sorted(grouped.items()):
        rates = {}
        for marker_name, marker in MASK_MARKERS.items():
            count = sum(
                marker.casefold() in row["text"].casefold()
                for row in group_rows
            )
            rates[marker_name] = round(count / len(group_rows), 4)
        output.setdefault(language, {})[label] = {
            "rows": len(group_rows),
            "rates": rates,
        }
    return output


def build_report(train_rows, validation_rows):
    return {
        "experiment": "multilingual_mask_marker_label_association_audit",
        "test_partition_read": False,
        "model_trained": False,
        "train": calculate_marker_rates(train_rows),
        "validation": calculate_marker_rates(validation_rows),
        "validation_by_language_and_label": calculate_language_label_marker_rates(
            validation_rows
        ),
        "interpretation": [
            "A marker-label association can make a synthetic dataset easier to classify.",
            "Mask markers describe values detected by regex; they are not verified entity types.",
            "Association does not prove that a marker caused the classifier decision.",
            "The initial holdout test partition is not read by this diagnostic.",
        ],
    }


def print_split(split_name, summary):
    print(f"\n{split_name.upper()} — redaction marker prevalence")
    print(f"Rows: {summary['rows']}")
    for label, label_summary in summary["by_label"].items():
        print(f"  {label.upper()} ({label_summary['rows']} rows)")
        for marker_name, values in label_summary["markers"].items():
            print(
                f"    {marker_name:<22} "
                f"{values['messages']:>5} "
                f"({values['rate']:.1%})"
            )


def main():
    try:
        train_rows = read_split(SPLIT_DIRECTORY / "train.csv")
        validation_rows = read_split(SPLIT_DIRECTORY / "validation.csv")
        report = build_report(train_rows, validation_rows)
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Mask-marker audit failed: {error}") from error

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)

    print("SOUL — multilingual redaction-marker association audit")
    print("Training rows:", len(train_rows))
    print("Validation rows:", len(validation_rows))
    print("Test partition read: no")
    print("Model trained: no")
    print_split("train", report["train"])
    print_split("validation", report["validation"])
    print("\nAggregate validation marker rates by language and label:")
    for language, label_groups in report["validation_by_language_and_label"].items():
        print(f"  {language}:")
        for label, values in label_groups.items():
            summary = ", ".join(
                f"{name}={rate:.0%}" for name, rate in values["rates"].items()
                if rate > 0
            )
            print(f"    {label}: n={values['rows']} {summary or '(no markers)'}")

    print("\nReport saved locally:", REPORT_PATH)
    print(
        "\nInterpretation: these are text-marker associations only, not "
        "proof of fraud, leakage or causal model behaviour."
    )


if __name__ == "__main__":
    main()
