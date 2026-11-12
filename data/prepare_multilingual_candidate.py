"""Prepare and split the multilingual candidate without split leakage.

Input:
    data/private/multilingual_candidates/anmolshrivastav_14lang_candidate_audit.csv

Outputs remain local under:
    data/private/multilingual_candidates/prepared/

The utility:
- masks candidate URLs, domains, email/UPI, phone-like, 12-digit and PAN-like values;
- groups by final masked model text;
- quarantines any masked-text group with conflicting source labels;
- collapses repeated same-language, same-label masked messages while retaining counts;
- keeps identical final model text in one 80/10/10 train/validation/test partition;
- stratifies approximate fold assignment by language x source label;
- prints aggregate counts only.

It does not train a model, map binary labels to SOUL's three-class target, or modify
the historical Mendeley dataset/split/model.

Run from the repository root:
    python data/prepare_multilingual_candidate.py
"""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from sklearn.model_selection import StratifiedGroupKFold

from audit_mendeley_privacy import detect_patterns
from create_masked_privacy_review import mask_candidates, neutralize_spreadsheet_formula
from audit_multilingual_candidate import script_profile


DATA_DIRECTORY = Path(__file__).resolve().parent
CANDIDATE_DIRECTORY = (
    DATA_DIRECTORY / "private" / "multilingual_candidates"
)
INPUT_PATH = (
    CANDIDATE_DIRECTORY / "anmolshrivastav_14lang_candidate_audit.csv"
)
OUTPUT_DIRECTORY = CANDIDATE_DIRECTORY / "prepared"
PREPARED_PATH = OUTPUT_DIRECTORY / "anmolshrivastav_14lang_prepared.csv"
QUARANTINE_PATH = OUTPUT_DIRECTORY / "anmolshrivastav_14lang_quarantine.csv"
SUMMARY_PATH = OUTPUT_DIRECTORY / "anmolshrivastav_14lang_split_summary.json"
SPLIT_DIRECTORY = OUTPUT_DIRECTORY / "splits"

LABELS = {"ham", "scam"}
SPLIT_NAMES = ("train", "validation", "test")
RANDOM_SEED = 42
N_SPLITS = 10

PREPARED_COLUMNS = [
    "record_id",
    "text",
    "source_dataset",
    "source_label",
    "label_task",
    "language",
    "script_profile",
    "source_type",
    "declared_license",
    "source_splits",
    "source_occurrences",
    "original_content_sha256",
    "model_text_sha256",
    "group_id",
    "has_email_upi_candidate",
    "has_url_domain_candidate",
    "has_phone_long_number_candidate",
    "has_twelve_digit_candidate",
    "has_pan_like_candidate",
    "has_residual_candidate_after_mask",
]

QUARANTINE_COLUMNS = [
    "quarantine_id",
    "reason",
    "source_labels",
    "languages",
    "source_splits",
    "source_occurrences",
    "model_text_sha256",
]


def normalise_text(text):
    return " ".join((text or "").casefold().split())


def sha256_text(text):
    return hashlib.sha256(normalise_text(text).encode("utf-8")).hexdigest()


def safe_read_rows(path=INPUT_PATH):
    if not path.is_file():
        raise FileNotFoundError(
            f"Candidate audit CSV not found: {path}. "
            "Run data/audit_multilingual_candidate.py first."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {
            "record_id",
            "text",
            "source_dataset",
            "source_split",
            "source_label",
            "label_task",
            "language",
            "script_profile",
            "source_type",
            "declared_license",
            "content_sha256",
            "has_email_upi_candidate",
            "has_url_domain_candidate",
            "has_phone_long_number_candidate",
            "has_twelve_digit_candidate",
            "has_pan_like_candidate",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Candidate audit CSV is missing columns: "
                + ", ".join(sorted(missing))
            )

        rows = list(reader)
    if not rows:
        raise ValueError("Candidate audit CSV has no records.")
    return rows


def prepare_rows(source_rows):
    """Mask rows, group final text, quarantine conflicts and collapse repeats."""
    grouped = defaultdict(list)
    stats = Counter()

    seen_ids = set()
    for row in source_rows:
        record_id = (row.get("record_id") or "").strip()
        if not record_id or record_id in seen_ids:
            raise ValueError("Candidate input contains a blank or duplicate record_id.")
        seen_ids.add(record_id)

        text = (row.get("text") or "").strip()
        label = (row.get("source_label") or "").strip().casefold()
        language = (row.get("language") or "").strip().casefold()
        if not text:
            raise ValueError("Candidate input contains blank message text.")
        if len(text) > 5000:
            raise ValueError("A candidate message exceeds the 5,000-character limit.")
        if label not in LABELS:
            raise ValueError(f"Unsupported candidate label: {label!r}")
        if not language:
            raise ValueError("Candidate input contains a blank language tag.")

        masked = neutralize_spreadsheet_formula(mask_candidates(text))
        model_hash = sha256_text(masked)
        flags = detect_patterns(text)
        residual_flags = detect_patterns(masked)

        prepared = {
            "record_id": record_id,
            "text": masked,
            "source_dataset": row["source_dataset"],
            "source_label": label,
            "label_task": row["label_task"],
            "language": language,
            "script_profile": script_profile(text),
            "source_type": row["source_type"],
            "declared_license": row["declared_license"],
            "source_split": (row.get("source_split") or "").strip().casefold(),
            "original_content_sha256": row["content_sha256"],
            "model_text_sha256": model_hash,
            "group_id": f"ML14G_{model_hash[:16]}",
            "has_email_upi_candidate": int(flags["email_upi"]),
            "has_url_domain_candidate": int(flags["url_domain"]),
            "has_phone_long_number_candidate": int(flags["phone_long_number"]),
            "has_twelve_digit_candidate": int(flags["twelve_digit"]),
            "has_pan_like_candidate": int(flags["pan_like"]),
            "has_residual_candidate_after_mask": int(any(residual_flags.values())),
        }
        grouped[model_hash].append(prepared)
        stats["source_rows"] += 1
        stats["rows_with_original_privacy_candidate"] += int(any(flags.values()))
        stats["rows_with_residual_candidate_after_mask"] += int(any(residual_flags.values()))

    output_rows = []
    quarantine = []
    for model_hash in sorted(grouped):
        members = grouped[model_hash]
        labels = {row["source_label"] for row in members}
        languages = {row["language"] for row in members}
        source_splits = {row["source_split"] for row in members}

        if len(labels) > 1:
            stats["masked_text_conflict_groups"] += 1
            stats["masked_text_conflict_rows"] += len(members)
            quarantine.append(
                {
                    "quarantine_id": f"MQ{len(quarantine) + 1:05d}",
                    "reason": "same_masked_text_conflicting_binary_labels",
                    "source_labels": ";".join(sorted(labels)),
                    "languages": ";".join(sorted(languages)),
                    "source_splits": ";".join(sorted(source_splits)),
                    "source_occurrences": len(members),
                    "model_text_sha256": model_hash,
                }
            )
            continue

        # Preserve one row per language tag, collapse repeated identical
        # masked text within the same source label + language.
        by_language = defaultdict(list)
        for row in members:
            by_language[row["language"]].append(row)

        for language in sorted(by_language):
            language_members = by_language[language]
            representative = dict(language_members[0])
            representative["record_id"] = f"ML14_{len(output_rows) + 1:06d}"
            representative["source_splits"] = ";".join(
                sorted({row["source_split"] for row in language_members})
            )
            representative["source_occurrences"] = len(language_members)
            representative.pop("source_split", None)
            output_rows.append(representative)

            if len(language_members) > 1:
                stats["same_language_masked_duplicate_groups_collapsed"] += 1
                stats["same_language_duplicate_rows_collapsed"] += len(language_members) - 1

        if len(languages) > 1:
            stats["same_masked_text_multiple_language_tags"] += 1
        if len(source_splits) > 1:
            stats["masked_text_groups_crossing_publisher_splits"] += 1

    stats["prepared_rows"] = len(output_rows)
    stats["quarantine_groups"] = len(quarantine)
    stats["quarantined_rows"] = sum(row["source_occurrences"] for row in quarantine)
    stats["unique_model_text_groups"] = len(
        {row["model_text_sha256"] for row in output_rows}
    )
    return output_rows, quarantine, stats


def create_grouped_splits(rows, seed=RANDOM_SEED):
    """Assign groups to 80/10/10 folds, stratified approximately by language x label."""
    if len(rows) < N_SPLITS:
        raise ValueError("At least 10 prepared rows are required for 10-fold splitting.")

    group_ids = [row["group_id"] for row in rows]
    strata = [f'{row["language"]}|{row["source_label"]}' for row in rows]
    unique_groups = set(group_ids)
    if len(unique_groups) < N_SPLITS:
        raise ValueError("At least 10 unique masked-text groups are required.")

    splitter = StratifiedGroupKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=seed,
    )

    folds = list(
        splitter.split(
            X=list(range(len(rows))),
            y=strata,
            groups=group_ids,
        )
    )
    assignments = {}
    for fold_index, (_train_indices, test_indices) in enumerate(folds):
        split_name = "test" if fold_index == 0 else "validation" if fold_index == 1 else "train"
        for index in test_indices:
            record_id = rows[index]["record_id"]
            assignments[record_id] = split_name

    if len(assignments) != len(rows):
        raise ValueError("Grouped split failed to assign every prepared record.")

    split_rows = {name: [] for name in SPLIT_NAMES}
    group_partition = {}
    for row in rows:
        split_name = assignments[row["record_id"]]
        split_rows[split_name].append({**row, "split": split_name})
        group_id = row["group_id"]
        if group_id in group_partition and group_partition[group_id] != split_name:
            raise ValueError("A masked-text group crossed SOUL split partitions.")
        group_partition[group_id] = split_name

    validate_grouped_splits(split_rows)
    return split_rows


def validate_grouped_splits(split_rows):
    seen_groups = {}
    seen_texts = {}
    for split_name, rows in split_rows.items():
        for row in rows:
            group_id = row["group_id"]
            text_hash = row["model_text_sha256"]
            if group_id in seen_groups and seen_groups[group_id] != split_name:
                raise ValueError("A group ID appears across multiple partitions.")
            if text_hash in seen_texts and seen_texts[text_hash] != split_name:
                raise ValueError("Identical masked model text appears across splits.")
            seen_groups[group_id] = split_name
            seen_texts[text_hash] = split_name
    return True


def aggregate_summary(rows, quarantine, split_rows, stats):
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dataset": "anmolshrivastav/scam_ham_india_14_languages",
        "task": "binary scam_vs_ham; labels are not mapped to SOUL three-class classes",
        "source_type": "synthetic",
        "model_trained": False,
        "historical_baseline_modified": False,
        "publisher_split_used_for_evaluation": False,
        "stats": dict(stats),
        "split_counts": {},
        "split_language_label_counts": {},
        "split_group_counts": {},
    }
    for split_name in SPLIT_NAMES:
        label_counts = Counter(row["source_label"] for row in split_rows[split_name])
        language_counts = Counter(row["language"] for row in split_rows[split_name])
        joint = Counter(f'{row["language"]}|{row["source_label"]}' for row in split_rows[split_name])
        summary["split_counts"][split_name] = {
            "rows": len(split_rows[split_name]),
            "labels": dict(sorted(label_counts.items())),
            "languages": dict(sorted(language_counts.items())),
        }
        summary["split_language_label_counts"][split_name] = dict(sorted(joint.items()))
        summary["split_group_counts"][split_name] = len(
            {row["group_id"] for row in split_rows[split_name]}
        )
    summary["quarantine_groups"] = len(quarantine)
    summary["quarantine_rows"] = sum(
        int(row["source_occurrences"]) for row in quarantine
    )
    summary["group_leakage_check"] = "passed"
    return summary


def write_outputs(rows, quarantine, split_rows, summary):
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    SPLIT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    with PREPARED_PATH.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=PREPARED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    with QUARANTINE_PATH.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=QUARANTINE_COLUMNS)
        writer.writeheader()
        writer.writerows(quarantine)

    split_columns = PREPARED_COLUMNS + ["split"]
    for split_name in SPLIT_NAMES:
        path = SPLIT_DIRECTORY / f"{split_name}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=split_columns)
            writer.writeheader()
            writer.writerows(split_rows[split_name])

    with SUMMARY_PATH.open("w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2, ensure_ascii=False)


def print_summary(summary):
    stats = summary["stats"]
    print("SOUL — multilingual candidate preparation and grouped split")
    print("Source rows:", stats["source_rows"])
    print("Prepared rows after masking/grouping:", stats["prepared_rows"])
    print("Unique final masked-text groups:", stats["unique_model_text_groups"])
    print("Rows with original privacy candidates:", stats["rows_with_original_privacy_candidate"])
    print("Rows with residual candidates after masking:", stats["rows_with_residual_candidate_after_mask"])
    print("Same-language duplicate groups collapsed:", stats["same_language_masked_duplicate_groups_collapsed"])
    print("Same-language duplicate rows collapsed:", stats["same_language_duplicate_rows_collapsed"])
    print("Masked-text groups crossing publisher splits:", stats["masked_text_groups_crossing_publisher_splits"])
    print("Masked-text groups with multiple language tags:", stats["same_masked_text_multiple_language_tags"])
    print("Masked-text conflicts quarantined:", stats["masked_text_conflict_groups"])
    print("Quarantined source rows:", summary["quarantine_rows"])

    print("\nSOUL grouped split:")
    for split_name in SPLIT_NAMES:
        split = summary["split_counts"][split_name]
        print(f"  {split_name}: {split['rows']} rows / {summary['split_group_counts'][split_name]} groups")
        print("    labels:", split["labels"])
        print("    languages:", split["languages"])

    print("\nIntegrity:")
    print("  Exact masked text/group crosses partitions: no")
    print("  Source publisher test set used as SOUL test: no")
    print("  Historical Mendeley baseline modified: no")
    print("  Model trained: no")
    print("  All row-level outputs remain under data/private/.")


def main():
    try:
        source_rows = safe_read_rows()
        rows, quarantine, stats = prepare_rows(source_rows)
        if not rows:
            raise ValueError("No prepared rows remain after conflict quarantine.")
        split_rows = create_grouped_splits(rows)
        summary = aggregate_summary(rows, quarantine, split_rows, stats)
        write_outputs(rows, quarantine, split_rows, summary)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(f"Multilingual candidate preparation failed: {error}") from error

    print_summary(summary)


if __name__ == "__main__":
    main()
