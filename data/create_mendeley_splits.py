"""Create deterministic, text-only, grouped train/validation/test splits.

Input:
    data/private/mendeley_prepared.csv

Outputs stay in:
    data/private/mendeley_splits/

Identical normalised masked texts are grouped before splitting. Same-label
masked duplicates collapse to one model row; cross-label masked-text groups
are quarantined. The split is stratified by class and uses a fixed seed.

This only prevents exact final-text leakage. It does not detect every
near-duplicate campaign and does not train or evaluate a model.

Run from the repository root:
    python data/create_mendeley_splits.py
"""

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parent
INPUT_PATH = DATA_DIRECTORY / "private" / "mendeley_prepared.csv"
OUTPUT_DIRECTORY = DATA_DIRECTORY / "private" / "mendeley_splits"
QUARANTINE_PATH = OUTPUT_DIRECTORY / "split_quarantine.csv"

SPLIT_RATIOS = {
    "train": 0.70,
    "validation": 0.15,
    "test": 0.15,
}
RANDOM_SEED = 42
ALLOWED_LABELS = {"legitimate", "scam", "spam"}


def normalise_text(text):
    """Use the exact model text, case-folded with repeated whitespace collapsed."""
    return " ".join((text or "").casefold().split())


def read_prepared_records(path=INPUT_PATH):
    if not path.is_file():
        raise FileNotFoundError(
            f"Prepared CSV not found: {path}\n"
            "Run data/prepare_mendeley_dataset.py first."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"record_id", "label", "text", "source_occurrences"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Prepared CSV is missing columns: "
                + ", ".join(sorted(missing))
            )
        return list(reader)


def group_model_texts(records):
    """Group identical final model inputs and quarantine conflicting targets."""
    grouped = defaultdict(list)

    for row in records:
        text = (row.get("text") or "").strip()
        label = (row.get("label") or "").strip().casefold()

        if not text:
            raise ValueError("Prepared data contains blank text.")
        if label not in ALLOWED_LABELS:
            raise ValueError(f"Prepared data contains an unsupported label: {label!r}")

        try:
            source_occurrences = int(row.get("source_occurrences", ""))
        except (TypeError, ValueError):
            raise ValueError("Prepared data contains an invalid source_occurrences value.")

        if source_occurrences < 1:
            raise ValueError("source_occurrences must be at least 1.")

        key = normalise_text(text)
        grouped[key].append(
            {
                "record_id": (row.get("record_id") or "").strip(),
                "label": label,
                "text": text,
                "source_occurrences": source_occurrences,
            }
        )

    model_groups = []
    quarantine = []
    stats = Counter()

    for key in sorted(grouped):
        members = grouped[key]
        labels = sorted({member["label"] for member in members})
        source_occurrences = sum(
            member["source_occurrences"] for member in members
        )

        if len(labels) > 1:
            stats["cross_label_groups_quarantined"] += 1
            stats["prepared_records_quarantined"] += len(members)
            stats["source_occurrences_quarantined"] += source_occurrences
            quarantine.append(
                {
                    "quarantine_id": f"Q{len(quarantine) + 1:05d}",
                    "reason": "same_masked_text_different_labels",
                    "prepared_records": len(members),
                    "source_occurrences": source_occurrences,
                    "source_labels": ";".join(labels),
                }
            )
            continue

        if len(members) > 1:
            stats["same_label_masked_groups_collapsed"] += 1
            stats["prepared_duplicate_records_collapsed"] += len(members) - 1

        model_groups.append(
            {
                "split_group_id": "",
                "record_id": "",
                "label": labels[0],
                "text": members[0]["text"],
                "source_occurrences": source_occurrences,
                "prepared_records_merged": len(members),
                "split": "",
            }
        )

    for index, group in enumerate(model_groups, start=1):
        group["split_group_id"] = f"G{index:05d}"
        group["record_id"] = f"S{index:05d}"

    stats["prepared_input_records"] = len(records)
    stats["unique_masked_text_groups"] = len(grouped)
    stats["model_rows_after_grouping"] = len(model_groups)
    stats["quarantine_groups"] = len(quarantine)
    return model_groups, quarantine, stats


def allocate_counts(total):
    """Return deterministic 70/15/15 counts, with all splits non-empty."""
    if total < 3:
        raise ValueError(
            "Each class needs at least three unique text groups for a "
            "non-empty train/validation/test split."
        )

    train_count = int(total * SPLIT_RATIOS["train"])
    validation_count = int(total * SPLIT_RATIOS["validation"])

    train_count = max(1, train_count)
    validation_count = max(1, validation_count)

    if train_count + validation_count >= total:
        train_count = total - 2
        validation_count = 1

    test_count = total - train_count - validation_count
    return train_count, validation_count, test_count


def create_splits(model_groups, seed=RANDOM_SEED):
    """Stratify by label; each unique masked-text group belongs to one split."""
    by_label = defaultdict(list)
    for group in model_groups:
        by_label[group["label"]].append(dict(group))

    splits = {
        "train": [],
        "validation": [],
        "test": [],
    }

    for label_index, label in enumerate(("legitimate", "scam", "spam")):
        class_groups = sorted(
            by_label[label],
            key=lambda group: group["split_group_id"],
        )
        if not class_groups:
            raise ValueError(f"No model groups available for class {label!r}.")

        rng = random.Random(seed + label_index)
        rng.shuffle(class_groups)

        train_count, validation_count, test_count = allocate_counts(
            len(class_groups)
        )
        boundaries = {
            "train": train_count,
            "validation": train_count + validation_count,
            "test": train_count + validation_count + test_count,
        }

        for index, group in enumerate(class_groups):
            if index < boundaries["train"]:
                split_name = "train"
            elif index < boundaries["validation"]:
                split_name = "validation"
            else:
                split_name = "test"

            group["split"] = split_name
            splits[split_name].append(group)

    for split_name in splits:
        splits[split_name].sort(
            key=lambda group: (group["label"], group["split_group_id"])
        )

    validate_splits(splits)
    return splits


def validate_splits(splits):
    """Raise if text or group IDs cross partitions or labels are invalid."""
    seen_texts = {}
    seen_groups = {}
    for split_name, rows in splits.items():
        for row in rows:
            if row["label"] not in ALLOWED_LABELS:
                raise ValueError("A split contains an invalid label.")
            key = normalise_text(row["text"])

            if key in seen_texts and seen_texts[key] != split_name:
                raise ValueError("Identical masked text appears in multiple splits.")
            seen_texts[key] = split_name

            group_id = row["split_group_id"]
            if group_id in seen_groups and seen_groups[group_id] != split_name:
                raise ValueError("A split group appears in multiple partitions.")
            seen_groups[group_id] = split_name


def write_splits(splits, quarantine, output_directory=OUTPUT_DIRECTORY):
    output_directory.mkdir(parents=True, exist_ok=True)

    split_columns = [
        "split_group_id",
        "record_id",
        "label",
        "text",
        "source_occurrences",
        "prepared_records_merged",
        "split",
    ]
    quarantine_columns = [
        "quarantine_id",
        "reason",
        "prepared_records",
        "source_occurrences",
        "source_labels",
    ]

    for split_name, rows in splits.items():
        output_path = output_directory / f"{split_name}.csv"
        with output_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=split_columns)
            writer.writeheader()
            writer.writerows(rows)

    quarantine_path = output_directory / "split_quarantine.csv"
    with quarantine_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=quarantine_columns)
        writer.writeheader()
        writer.writerows(quarantine)


def print_summary(splits, quarantine, stats):
    print("SOUL — deterministic grouped dataset split")
    print("Prepared input records:", stats["prepared_input_records"])
    print("Unique masked-text groups:", stats["unique_masked_text_groups"])
    print("Same-label groups collapsed:", stats["same_label_masked_groups_collapsed"])
    print("Prepared duplicate rows collapsed:", stats["prepared_duplicate_records_collapsed"])
    print("Cross-label groups quarantined:", stats["cross_label_groups_quarantined"])
    print("Prepared rows quarantined:", stats["prepared_records_quarantined"])
    print("Source occurrences quarantined:", stats["source_occurrences_quarantined"])
    print("Final model rows:", stats["model_rows_after_grouping"])

    print("\nSplit class counts:")
    print("  SPLIT       TOTAL  LEGITIMATE  SCAM  SPAM")
    for split_name in ("train", "validation", "test"):
        counts = Counter(row["label"] for row in splits[split_name])
        print(
            f"  {split_name:<11} "
            f"{len(splits[split_name]):>5} "
            f"{counts['legitimate']:>11} "
            f"{counts['scam']:>5} "
            f"{counts['spam']:>5}"
        )

    print("\nSplit sizes:")
    total = sum(len(rows) for rows in splits.values())
    for split_name in ("train", "validation", "test"):
        count = len(splits[split_name])
        percentage = count / total * 100 if total else 0
        print(f"  {split_name}: {count} ({percentage:.1f}%)")

    print("\nIntegrity checks:")
    print("  Identical masked text crosses splits: no")
    print("  Split group crosses partitions: no")
    print("  Model inputs: text only; label is target")

    print("\nOutput directory:", OUTPUT_DIRECTORY)
    print(
        "Note: Exact masked-text grouping prevents exact-text leakage only. "
        "It does not detect near-duplicate campaigns. Use these results as "
        "an exploratory split, not proof of real-world generalisation."
    )


def main():
    try:
        prepared_records = read_prepared_records()
        model_groups, quarantine, stats = group_model_texts(prepared_records)
        splits = create_splits(model_groups, seed=RANDOM_SEED)
        write_splits(splits, quarantine)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(f"Dataset splitting failed: {error}") from error

    print_summary(splits, quarantine, stats)


if __name__ == "__main__":
    main()
