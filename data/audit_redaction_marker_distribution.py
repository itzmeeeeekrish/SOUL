"""Audit redaction-marker prevalence in the frozen baseline splits.

Run from the repository root:
    python data/audit_redaction_marker_distribution.py

Reads only train.csv and validation.csv plus the saved baseline split hashes.
It does not read test.csv, train a model, tune parameters, or export message text.
All outputs are aggregate counts under Git-ignored data/private/.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

from train_text_baseline import (
    ARTIFACT_DIRECTORY,
    LABEL_ORDER,
    METRICS_PATH,
    SPLIT_DIRECTORY,
    read_split,
    sha256_file,
)

REPORT_PATH = ARTIFACT_DIRECTORY / "redaction_marker_distribution.json"
AUDITED_SPLITS = ("train", "validation")
MARKERS = {
    "url": "[URL]",
    "domain": "[DOMAIN]",
    "email_or_upi": "[EMAIL_OR_UPI]",
    "pan_like": "[PAN_LIKE]",
    "twelve_digit_number": "[12_DIGIT_NUMBER]",
    "long_number": "[LONG_NUMBER]",
}


def build_marker_distribution(splits):
    """Return per-class marker document counts/rates without copying messages."""
    if not isinstance(splits, dict):
        raise ValueError("Splits must be provided as a mapping.")
    if set(splits) != set(AUDITED_SPLITS):
        raise ValueError("Only train and validation splits are allowed.")

    report = {
        "schema_version": 1,
        "splits": {},
        "privacy": {
            "message_text_exported": False,
            "row_ids_exported": False,
            "only_aggregate_counts": True,
        },
        "scope": {
            "train_split_read": True,
            "validation_split_read": True,
            "test_split_read": False,
            "model_retrained": False,
            "parameters_or_thresholds_tuned": False,
        },
        "interpretation": (
            "Prevalence is the share of messages in each split/class containing "
            "a redaction placeholder. It measures a data association, not causal "
            "importance or fraud intent. The vectorizer token for [LONG_NUMBER] "
            "is typically 'long_number'."
        ),
    }

    for split_name in AUDITED_SPLITS:
        rows = splits[split_name]
        if not rows:
            raise ValueError(f"{split_name} split must not be empty.")

        by_label = {
            label: {
                "support": 0,
                "markers": {
                    marker_name: {"messages_with_marker": 0, "prevalence": 0.0}
                    for marker_name in MARKERS
                },
                "messages_with_any_marker": 0,
            }
            for label in LABEL_ORDER
        }

        for row in rows:
            label = str(row.get("label") or "")
            text = str(row.get("text") or "")
            if label not in LABEL_ORDER:
                raise ValueError(f"{split_name} contains an unsupported label.")
            if not text.strip():
                raise ValueError(f"{split_name} contains blank message text.")

            stats = by_label[label]
            stats["support"] += 1
            any_marker = False
            folded_text = text.casefold()
            for marker_name, marker in MARKERS.items():
                present = marker.casefold() in folded_text
                if present:
                    stats["markers"][marker_name]["messages_with_marker"] += 1
                    any_marker = True
            if any_marker:
                stats["messages_with_any_marker"] += 1

        for label, stats in by_label.items():
            support = stats["support"]
            for marker_stats in stats["markers"].values():
                count = marker_stats["messages_with_marker"]
                marker_stats["prevalence"] = (
                    round(count / support, 6) if support else None
                )
            stats["any_marker_prevalence"] = (
                round(stats["messages_with_any_marker"] / support, 6)
                if support
                else None
            )

        report["splits"][split_name] = {
            "total_rows": len(rows),
            "by_label": by_label,
        }

    return report


def main():
    if not METRICS_PATH.is_file():
        raise SystemExit(
            "Baseline metrics not found. Run data/train_text_baseline.py "
            "before this audit."
        )

    try:
        metadata = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        expected_hashes = metadata.get("split_sha256", {})
        splits = {}
        for split_name in AUDITED_SPLITS:
            path = SPLIT_DIRECTORY / f"{split_name}.csv"
            expected_hash = expected_hashes.get(split_name)
            if not expected_hash or expected_hash != sha256_file(path):
                raise ValueError(
                    f"{split_name}.csv does not match the frozen baseline fingerprint."
                )
            splits[split_name] = read_split(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Redaction-marker audit stopped: {error}") from error

    report = build_marker_distribution(splits)
    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("SOUL — redaction-marker prevalence audit")
    print("Source: frozen train + validation partitions only")
    for split_name in AUDITED_SPLITS:
        print(f"\n{split_name.upper()}")
        split_report = report["splits"][split_name]["by_label"]
        for label in LABEL_ORDER:
            stats = split_report[label]
            print(
                f"  {label}: {stats['support']} messages; "
                f"any marker={stats['messages_with_any_marker']} "
                f"({stats['any_marker_prevalence']:.2%})"
            )
            for marker_name, marker_stats in stats["markers"].items():
                count = marker_stats["messages_with_marker"]
                if count:
                    print(
                        f"    {marker_name}: {count} "
                        f"({marker_stats['prevalence']:.2%})"
                    )

    print("\nLocal report:", REPORT_PATH)
    print("Privacy: aggregate counts only; no message text or IDs exported.")
    print("Scope: no test split, no retraining, no tuning.")


if __name__ == "__main__":
    main()
