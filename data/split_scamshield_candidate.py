"""Create deterministic group-safe train/validation/test splits for ScamShield.

Input must be the private three-class silver preview created by
data/prepare_scamshield_candidate.py. Exact masked-text duplicates have already
been collapsed into one row. This script verifies that invariant and creates
an 80/10/10 stratified split while preserving language/class strata where
there are enough examples.

This is an internal mixed-source evaluation split, NOT a source-held-out,
independent, or real-world evaluation set. Labels remain provisional silver
labels and must not be described as human-verified ground truth.

Run from the repository root:
    python data/split_scamshield_candidate.py
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.model_selection import train_test_split


DATA_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_INPUT = (
    DATA_DIRECTORY / "private" / "scamshield_candidate" / "curation"
    / "scamshield_three_class_silver_preview.csv"
)
DEFAULT_OUTPUT_DIRECTORY = (
    DATA_DIRECTORY / "private" / "scamshield_candidate" / "splits"
)

EXPECTED_LABELS = {"legitimate", "spam", "scam"}
REQUIRED_COLUMNS = {
    "model_row_id",
    "text",
    "label",
    "label_provenance",
    "masked_text_sha256",
    "languages_json",
    "source_datasets_json",
    "cross_source_duplicate_group",
}
DEFAULT_SEED = 42
MIN_LANGUAGE_CLASS_GROUP_SIZE = 10


def _json_string_list(value, field_name):
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON in {field_name}: {error}") from error
    if not isinstance(parsed, list) or not parsed:
        raise ValueError(f"{field_name} must be a non-empty JSON list.")
    if any(not isinstance(item, str) or not item.strip() for item in parsed):
        raise ValueError(f"{field_name} must contain non-empty strings only.")
    return sorted(set(item.strip().casefold() for item in parsed))


def load_candidate_rows(input_path=DEFAULT_INPUT):
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Candidate CSV not found: {input_path}. "
            "Run data/prepare_scamshield_candidate.py first."
        )

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                "Candidate CSV is missing columns: "
                + ", ".join(sorted(missing))
            )
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows:
        raise ValueError("Candidate CSV contains no rows.")

    seen_hashes = set()
    seen_ids = set()
    for row in rows:
        row_id = str(row["model_row_id"]).strip()
        text_hash = str(row["masked_text_sha256"]).strip()
        if not row_id or not text_hash:
            raise ValueError("Candidate CSV contains a blank ID or masked hash.")
        if row_id in seen_ids:
            raise ValueError(f"Duplicate model_row_id: {row_id}")
        if text_hash in seen_hashes:
            raise ValueError(
                "Candidate CSV still contains duplicate masked-text hashes; "
                "re-run curation before splitting."
            )
        seen_ids.add(row_id)
        seen_hashes.add(text_hash)

        if row["label"] not in EXPECTED_LABELS:
            raise ValueError(
                f"Unexpected candidate label {row['label']!r} for {row_id}."
            )
        if not str(row["text"] or "").strip():
            raise ValueError(f"Blank candidate text for {row_id}.")

        languages = _json_string_list(row["languages_json"], "languages_json")
        if len(languages) != 1:
            raise ValueError(
                f"Candidate {row_id} has conflicting language tags; "
                "it should have been sent to needs_review."
            )
        row["_language"] = languages[0]
        row["_sources"] = _json_string_list(
            row["source_datasets_json"], "source_datasets_json"
        )

    return rows, fieldnames


def build_stratification_keys(rows):
    """Stratify by label+language for adequately sized slices.

    Very small language/class slices are merged into a per-label rare-language
    stratum to avoid impossible or unstable stratified split requests.
    """
    raw_keys = [
        (row["label"], row["_language"])
        for row in rows
    ]
    counts = Counter(raw_keys)
    keys = []
    for label, language in raw_keys:
        if counts[(label, language)] >= MIN_LANGUAGE_CLASS_GROUP_SIZE:
            keys.append(f"{label}::{language}")
        else:
            keys.append(f"{label}::__rare_language__")
    return keys, counts


def make_splits(rows, seed=DEFAULT_SEED):
    if len(rows) < 30:
        raise ValueError("At least 30 candidate groups are required to split.")

    stratification_keys, raw_strata_counts = build_stratification_keys(rows)
    indices = list(range(len(rows)))

    try:
        train_indices, holdout_indices = train_test_split(
            indices,
            test_size=0.20,
            random_state=seed,
            stratify=stratification_keys,
        )
        holdout_keys = [stratification_keys[index] for index in holdout_indices]
        validation_indices, test_indices = train_test_split(
            holdout_indices,
            test_size=0.50,
            random_state=seed + 1,
            stratify=holdout_keys,
        )
    except ValueError as error:
        raise ValueError(
            "Could not create a stratified 80/10/10 split. "
            "The class/language distribution may be too sparse: "
            f"{error}"
        ) from error

    splits = {
        "train": [rows[index] for index in train_indices],
        "validation": [rows[index] for index in validation_indices],
        "test": [rows[index] for index in test_indices],
    }

    # Defensive postconditions: every candidate group appears exactly once.
    split_hashes = {
        name: [row["masked_text_sha256"] for row in split_rows]
        for name, split_rows in splits.items()
    }
    for first_name, first_hashes in split_hashes.items():
        if len(first_hashes) != len(set(first_hashes)):
            raise AssertionError(f"Duplicate masked hash inside {first_name}.")
        for second_name, second_hashes in split_hashes.items():
            if first_name >= second_name:
                continue
            if set(first_hashes) & set(second_hashes):
                raise AssertionError(
                    f"Masked-text group leakage between {first_name} "
                    f"and {second_name}."
                )

    assigned_ids = [
        row["model_row_id"]
        for split_rows in splits.values()
        for row in split_rows
    ]
    expected_ids = [row["model_row_id"] for row in rows]
    if Counter(assigned_ids) != Counter(expected_ids):
        raise AssertionError("Split assignment lost or duplicated candidate rows.")

    return splits, raw_strata_counts


def _count_by(splits, extractor):
    result = {}
    for split_name, rows in splits.items():
        counter = Counter()
        for row in rows:
            values = extractor(row)
            if isinstance(values, str):
                values = [values]
            counter.update(values)
        result[split_name] = dict(sorted(counter.items()))
    return result


def build_manifest(splits, raw_strata_counts, seed, input_path):
    return {
        "dataset_id": "sidzzz07/scamshield-dataset",
        "input_preview": str(input_path),
        "split_method": (
            "Deterministic 80/10/10 stratified random split over unique "
            "masked-text groups; stratification uses label+language when "
            "the slice has at least 10 groups, otherwise a per-label "
            "rare-language bucket."
        ),
        "random_seed": seed,
        "split_group_unit": "unique masked_text_sha256",
        "exact_masked_text_overlap_between_splits": False,
        "publisher_split_used": False,
        "source_disjointness_enforced": False,
        "unseen_source_evaluation_created": False,
        "independent_external_test_created": False,
        "real_world_test_created": False,
        "labels_are_provisional_silver": True,
        "human_verified_ground_truth": False,
        "license_review_complete": False,
        "split_row_counts": {
            name: len(rows) for name, rows in splits.items()
        },
        "class_counts_by_split": _count_by(
            splits, lambda row: row["label"]
        ),
        "language_counts_by_split": _count_by(
            splits, lambda row: row["_language"]
        ),
        "source_group_counts_by_split": _count_by(
            splits, lambda row: row["_sources"]
        ),
        "language_class_strata_before_rare_bucketing": {
            f"{label}::{language}": count
            for (label, language), count in sorted(raw_strata_counts.items())
        },
        "note": (
            "This test split measures performance on a random holdout from "
            "the same mixed-source candidate corpus. It does not establish "
            "generalisation to unseen sources, real-world messages, or "
            "independently verified labels."
        ),
    }


def write_split_outputs(splits, manifest, fieldnames, output_directory):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    outputs = {}
    for name, rows in splits.items():
        path = output_directory / f"scamshield_{name}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    field: row.get(field, "")
                    for field in fieldnames
                })
        outputs[name] = path

    manifest["outputs"] = {name: str(path) for name, path in outputs.items()}
    manifest_path = output_directory / "scamshield_split_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    outputs["manifest"] = manifest_path
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    try:
        rows, fieldnames = load_candidate_rows(args.input_csv)
        splits, raw_strata_counts = make_splits(rows, seed=args.seed)
        manifest = build_manifest(
            splits, raw_strata_counts, args.seed, args.input_csv
        )
        outputs = write_split_outputs(
            splits, manifest, fieldnames, args.output_dir
        )
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"ScamShield split creation failed: {error}") from error

    print("SOUL — ScamShield deterministic group-safe split")
    print("Unique candidate groups:", len(rows))
    print("Split row counts:", manifest["split_row_counts"])
    print("Class counts by split:")
    for split_name, counts in manifest["class_counts_by_split"].items():
        print(f"  {split_name}: {counts}")
    print("Language counts by split:")
    for split_name, counts in manifest["language_counts_by_split"].items():
        print(f"  {split_name}: {counts}")
    print("Exact masked-text leakage:", "none")
    print("Publisher split used: no")
    print("Source-disjoint holdout: no")
    print("Independent/real-world test: no")
    print("Human-verified labels: no")
    print("\nPrivate outputs:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
