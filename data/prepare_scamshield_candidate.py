"""Create a provenance-preserving ScamShield curation preview.

Reads only the masked audit CSV. It does not download data, reinterpret the
publisher's binary label directly, create train/validation/test splits, or train
a model. Rule-mapped labels remain provisional silver labels.

Run from repository root:
    python data/prepare_scamshield_candidate.py
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_INPUT = (
    DATA_DIRECTORY / "private" / "scamshield_candidate"
    / "scamshield_candidate_audit_masked.csv"
)
DEFAULT_OUTPUT_DIRECTORY = (
    DATA_DIRECTORY / "private" / "scamshield_candidate" / "curation"
)

REQUIRED_COLUMNS = {
    "record_id",
    "text",
    "source_dataset",
    "language",
    "source_split",
    "source_label_is_scam",
    "source_scam_intent",
    "source_split_group",
    "masked_text_sha256",
    "taxonomy_label_preview",
    "has_residual_candidate_after_mask",
}

CANDIDATE_COLUMNS = [
    "model_row_id",
    "text",
    "label",
    "label_provenance",
    "masked_text_sha256",
    "occurrence_count",
    "source_datasets_json",
    "languages_json",
    "source_intents_json",
    "source_binary_labels_json",
    "publisher_splits_json",
    "source_split_groups_json",
    "record_ids_json",
    "cross_source_duplicate_group",
    "cross_publisher_split_duplicate_group",
]

REVIEW_COLUMNS = CANDIDATE_COLUMNS + ["curation_reasons"]

QUARANTINE_COLUMNS = [
    "record_id",
    "text",
    "source_dataset",
    "language",
    "source_split",
    "source_label_is_scam",
    "source_scam_intent",
    "masked_text_sha256",
    "taxonomy_label_preview",
    "has_residual_candidate_after_mask",
    "curation_action",
    "curation_reasons",
]

KNOWN_LABELS = {"legitimate", "spam", "scam"}


def normalise_text(value):
    return " ".join(str(value or "").casefold().split())


def sha256_text(value):
    return hashlib.sha256(normalise_text(value).encode("utf-8")).hexdigest()


def parse_binary(value, field_name):
    text = str(value).strip()
    if text not in {"0", "1"}:
        raise ValueError(f"Invalid {field_name}: {value!r}")
    return int(text)


def parse_flag(value, field_name):
    text = str(value).strip().casefold()
    if text in {"1", "true"}:
        return True
    if text in {"0", "false", ""}:
        return False
    raise ValueError(f"Invalid {field_name}: {value!r}")


def load_audit_rows(input_path=DEFAULT_INPUT):
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(
            f"Masked audit CSV not found: {input_path}. "
            "Run data/audit_scamshield_candidate.py first."
        )

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                "Masked audit CSV is missing columns: "
                + ", ".join(sorted(missing))
            )
        rows = list(reader)

    if not rows:
        raise ValueError("Masked audit CSV contains no records.")

    seen_ids = set()
    for row in rows:
        record_id = str(row["record_id"]).strip()
        if not record_id:
            raise ValueError("Masked audit CSV contains a blank record_id.")
        if record_id in seen_ids:
            raise ValueError(f"Duplicate audit record_id: {record_id}")
        seen_ids.add(record_id)

        text = str(row["text"] or "")
        if not normalise_text(text):
            raise ValueError(f"Blank masked text for record_id {record_id}.")
        expected_hash = sha256_text(text)
        if row["masked_text_sha256"] != expected_hash:
            raise ValueError(
                f"Masked text hash mismatch for record_id {record_id}."
            )

        parse_binary(row["source_label_is_scam"], "source_label_is_scam")
        parse_flag(
            row["has_residual_candidate_after_mask"],
            "has_residual_candidate_after_mask",
        )
        row["taxonomy_label_preview"] = str(
            row["taxonomy_label_preview"] or "needs_review"
        ).strip().casefold()
        row["source_scam_intent"] = str(
            row["source_scam_intent"] or "missing"
        ).strip().casefold()
        row["source_dataset"] = str(
            row["source_dataset"] or "unknown"
        ).strip()
        row["language"] = str(row["language"] or "unknown").strip().casefold()
        row["source_split"] = str(row["source_split"] or "unknown").strip()
        row["source_split_group"] = str(
            row["source_split_group"] or ""
        ).strip()

    return rows


def json_values(values):
    return json.dumps(sorted(set(values)), ensure_ascii=False)


def classify_group(members):
    """Return action and reasons for one identical-masked-text group."""
    reasons = set()

    if any(
        parse_flag(row["has_residual_candidate_after_mask"],
                  "has_residual_candidate_after_mask")
        for row in members
    ):
        reasons.add("residual_privacy_pattern_after_mask")

    binary_labels = {
        parse_binary(row["source_label_is_scam"], "source_label_is_scam")
        for row in members
    }
    if len(binary_labels) > 1:
        reasons.add("conflicting_source_binary_labels")

    taxonomy_labels = {
        row["taxonomy_label_preview"]
        for row in members
        if row["taxonomy_label_preview"] in KNOWN_LABELS
    }
    if len(taxonomy_labels) > 1:
        reasons.add("conflicting_three_class_taxonomy_labels")

    for row in members:
        binary_label = parse_binary(
            row["source_label_is_scam"], "source_label_is_scam"
        )
        taxonomy_label = row["taxonomy_label_preview"]
        if taxonomy_label in KNOWN_LABELS:
            expected = "legitimate" if binary_label == 0 else None
            if binary_label == 0 and taxonomy_label != expected:
                reasons.add("source_binary_intent_semantic_mismatch")
            elif binary_label == 1 and taxonomy_label == "legitimate":
                reasons.add("source_binary_intent_semantic_mismatch")

    normalised_texts = {normalise_text(row["text"]) for row in members}
    if len(normalised_texts) > 1:
        reasons.add("masked_hash_collision_or_inconsistent_text")

    if reasons:
        return "quarantine", sorted(reasons)

    languages = {row["language"] for row in members}
    if len(languages) > 1:
        return "needs_review", ["conflicting_language_tags"]

    if any(row["taxonomy_label_preview"] not in KNOWN_LABELS for row in members):
        return "needs_review", ["unmapped_or_ambiguous_source_intent"]

    if len(taxonomy_labels) != 1:
        return "needs_review", ["missing_three_class_taxonomy"]

    return "candidate", []


def aggregate_group(members, label, reasons=None):
    first = members[0]
    sources = {row["source_dataset"] for row in members}
    splits = {row["source_split"] for row in members}
    source_groups = {
        f"{row['source_dataset']}::{row['source_split_group']}"
        for row in members
        if row["source_split_group"]
    }
    record_ids = {row["record_id"] for row in members}
    group_hash = first["masked_text_sha256"]

    result = {
        "model_row_id": "SS_" + group_hash[:16],
        "text": first["text"],
        "label": label,
        "label_provenance": (
            "source_intent_rule_mapping_v1; provisional_silver_not_human_verified"
        ) if label in KNOWN_LABELS else "unmapped_source_intent_or_metadata_conflict",
        "masked_text_sha256": group_hash,
        "occurrence_count": len(members),
        "source_datasets_json": json_values(sources),
        "languages_json": json_values(row["language"] for row in members),
        "source_intents_json": json_values(
            row["source_scam_intent"] for row in members
        ),
        "source_binary_labels_json": json_values(
            str(parse_binary(row["source_label_is_scam"],
                             "source_label_is_scam"))
            for row in members
        ),
        "publisher_splits_json": json_values(splits),
        "source_split_groups_json": json_values(source_groups),
        "record_ids_json": json_values(record_ids),
        "cross_source_duplicate_group": int(len(sources) > 1),
        "cross_publisher_split_duplicate_group": int(len(splits) > 1),
    }
    if reasons:
        result["curation_reasons"] = json.dumps(reasons, ensure_ascii=False)
    return result


def curate_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["masked_text_sha256"]].append(row)

    candidates = []
    review = []
    quarantine = []
    action_counts = Counter()
    reason_counts = Counter()
    candidate_class_counts = Counter()
    candidate_language_counts = Counter()
    candidate_source_counts = Counter()

    for group_hash in sorted(groups):
        members = groups[group_hash]
        action, reasons = classify_group(members)
        action_counts[action] += 1
        reason_counts.update(reasons)

        if action == "candidate":
            label = next(iter({
                row["taxonomy_label_preview"] for row in members
            }))
            aggregate = aggregate_group(members, label)
            candidates.append(aggregate)
            candidate_class_counts[label] += 1
            candidate_language_counts.update(
                json.loads(aggregate["languages_json"])
            )
            candidate_source_counts.update(
                json.loads(aggregate["source_datasets_json"])
            )
        elif action == "needs_review":
            review.append(
                aggregate_group(members, "needs_review", reasons=reasons)
            )
        else:
            for row in members:
                quarantine.append({
                    key: row.get(key, "")
                    for key in QUARANTINE_COLUMNS
                    if key not in {"curation_action", "curation_reasons"}
                } | {
                    "curation_action": "quarantine",
                    "curation_reasons": json.dumps(reasons, ensure_ascii=False),
                })

    summary = {
        "input_rows": len(rows),
        "unique_masked_text_groups": len(groups),
        "candidate_groups": len(candidates),
        "candidate_source_occurrences": sum(
            int(row["occurrence_count"]) for row in candidates
        ),
        "needs_review_groups": len(review),
        "needs_review_source_occurrences": sum(
            int(row["occurrence_count"]) for row in review
        ),
        "quarantined_groups": action_counts["quarantine"],
        "quarantined_source_rows": len(quarantine),
        "duplicate_occurrences_collapsed_in_candidates": sum(
            int(row["occurrence_count"]) - 1 for row in candidates
        ),
        "candidate_class_counts": dict(sorted(candidate_class_counts.items())),
        "candidate_language_group_counts": dict(
            sorted(candidate_language_counts.items())
        ),
        "candidate_source_group_counts": dict(
            sorted(candidate_source_counts.items())
        ),
        "cross_source_candidate_groups": sum(
            int(row["cross_source_duplicate_group"]) for row in candidates
        ),
        "cross_publisher_split_candidate_groups": sum(
            int(row["cross_publisher_split_duplicate_group"])
            for row in candidates
        ),
        "action_group_counts": dict(sorted(action_counts.items())),
        "quarantine_reason_group_counts": dict(sorted(reason_counts.items())),
        "training_labels_are_provisional_silver": True,
        "human_verified_ground_truth": False,
        "license_review_complete": False,
        "train_validation_test_split_created": False,
        "model_trained": False,
    }
    return candidates, review, quarantine, summary


def write_curation_outputs(
    candidates,
    review,
    quarantine,
    summary,
    output_directory=DEFAULT_OUTPUT_DIRECTORY,
):
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    outputs = {
        "candidate": output_directory / "scamshield_three_class_silver_preview.csv",
        "review": output_directory / "scamshield_needs_review.csv",
        "quarantine": output_directory / "scamshield_quarantine.csv",
    }

    for key, rows in (
        ("candidate", candidates),
        ("review", review),
        ("quarantine", quarantine),
    ):
        if key == "candidate":
            columns = CANDIDATE_COLUMNS
        elif key == "review":
            columns = REVIEW_COLUMNS
        else:
            columns = QUARANTINE_COLUMNS
        with outputs[key].open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    manifest = {
        "dataset_id": "sidzzz07/scamshield-dataset",
        "method": (
            "Deterministic source-intent taxonomy preview, grouped by final "
            "masked-text hash; no model training or split creation."
        ),
        "label_status": (
            "Provisional silver labels from source intent names; not "
            "independently human-verified ground truth."
        ),
        "privacy_status": (
            "Residual-pattern rows are quarantined. Regex screening does not "
            "prove complete anonymisation."
        ),
        "source_status": (
            "Source-level upstream licence and provenance review remains pending."
        ),
        "summary": summary,
        "outputs": {key: str(path) for key, path in outputs.items()},
    }
    summary_path = output_directory / "scamshield_curation_summary.json"
    summary_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    outputs["summary"] = summary_path
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    args = parser.parse_args()

    try:
        rows = load_audit_rows(args.input_csv)
        candidates, review, quarantine, summary = curate_rows(rows)
        outputs = write_curation_outputs(
            candidates, review, quarantine, summary, args.output_dir
        )
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"ScamShield curation preview failed: {error}") from error

    print("SOUL — ScamShield three-class curation preview")
    print("Input rows:", summary["input_rows"])
    print("Unique masked-text groups:", summary["unique_masked_text_groups"])
    print("Candidate groups:", summary["candidate_groups"])
    print("Provisional class counts:", summary["candidate_class_counts"])
    print("Needs-review groups:", summary["needs_review_groups"])
    print("Quarantined groups:", summary["quarantined_groups"])
    print("Quarantined source rows:", summary["quarantined_source_rows"])
    print(
        "Duplicate occurrences collapsed in candidate groups:",
        summary["duplicate_occurrences_collapsed_in_candidates"],
    )
    print("Cross-source candidate groups:", summary["cross_source_candidate_groups"])
    print("Cross-publisher-split candidate groups:",
          summary["cross_publisher_split_candidate_groups"])
    print("Quarantine reasons:", summary["quarantine_reason_group_counts"])
    print("Train/validation/test split created: no")
    print("Model trained: no")
    print("Human-verified ground truth: no")
    print("\nPrivate outputs:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
