"""Audit the ScamShield multilingual corpus without training a model.

Downloads the public Hugging Face dataset into the local cache, masks
candidate identifiers, and writes row-level data only under Git-ignored
data/private/scamshield_candidate/. Aggregate output reports source, language,
intent, duplicate, split-group and privacy-pattern distributions.

The positive is_scam class includes the source intent
General Spam / Telemarketing in displayed examples. This audit preserves
source labels and does not approve them as SOUL fraud ground truth.

Run from repository root:
    python data/audit_scamshield_candidate.py

Optional dependency:
    python -m pip install datasets
"""

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from audit_mendeley_privacy import detect_patterns
    from create_masked_privacy_review import (
        mask_candidates,
        neutralize_spreadsheet_formula,
    )
    from audit_multilingual_candidate import script_profile
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from audit_mendeley_privacy import detect_patterns
    from create_masked_privacy_review import (
        mask_candidates,
        neutralize_spreadsheet_formula,
    )
    from audit_multilingual_candidate import script_profile


DATASET_ID = "sidzzz07/scamshield-dataset"
DATASET_DIRECTORY = (
    Path(__file__).resolve().parent / "private" / "scamshield_candidate"
)
OUTPUT_CSV = DATASET_DIRECTORY / "scamshield_candidate_audit_masked.csv"
OUTPUT_JSON = DATASET_DIRECTORY / "scamshield_candidate_audit_summary.json"

KNOWN_SPLITS = {"train", "val", "validation", "test"}
PRIVACY_FIELDS = (
    "email_upi",
    "url_domain",
    "phone_long_number",
    "twelve_digit",
    "pan_like",
)
METADATA_FLAGS = ("has_url", "has_phone", "has_otp", "has_upi", "has_amount")
SOCIAL_FLAGS = (
    "urgency",
    "fear",
    "authority_impersonation",
    "reward_bait",
    "financial_pressure",
)
SCAM_INTENTS = {
    "bank account freeze",
    "courier scam",
    "electricity disconnection",
    "fake kyc",
    "loan scam",
    "lottery / prize",
    "otp / credential theft",
    "telegram job",
    "traffic e-challan",
    "upi fraud",
}

OUTPUT_COLUMNS = [
    "record_id",
    "source_id",
    "text",
    "source_dataset",
    "language",
    "source_split",
    "source_label_is_scam",
    "source_scam_intent",
    "source_split_group",
    "content_sha256",
    "masked_text_sha256",
    "script_profile",
    "source_type_hint",
    "record_id_prefix_hint",
    "taxonomy_label_preview",
    "has_email_upi_candidate",
    "has_url_domain_candidate",
    "has_phone_long_number_candidate",
    "has_twelve_digit_candidate",
    "has_pan_like_candidate",
    "has_residual_candidate_after_mask",
    *[f"residual_{name}_candidate" for name in PRIVACY_FIELDS],
    *[f"metadata_{name}" for name in METADATA_FLAGS],
    *[f"social_{name}" for name in SOCIAL_FLAGS],
]


def normalise_text(value):
    return " ".join(str(value or "").casefold().split())


def sha256_text(value):
    return hashlib.sha256(normalise_text(value).encode("utf-8")).hexdigest()


def normalise_binary_label(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and value in (0, 1):
        return value
    if isinstance(value, str):
        value = value.strip().casefold()
        if value in {"0", "false", "ham", "benign", "legitimate"}:
            return 0
        if value in {"1", "true", "scam", "fraud"}:
            return 1
    raise ValueError(f"Unsupported is_scam value: {value!r}")


def safe_flag(mapping, name):
    if not isinstance(mapping, dict):
        return 0
    value = mapping.get(name, False)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and value in (0, 1):
        return value
    return 0


def source_type_hint(source_dataset):
    value = str(source_dataset or "").casefold()
    if "synthetic" in value:
        return "synthetic_named_source"
    if value:
        return "non_synthetic_named_source_unverified"
    return "unknown_source"


def record_id_prefix_hint(source_id):
    """Classify only the visible ID prefix; it is not verified provenance."""
    value = str(source_id or "").strip().casefold()
    if value.startswith("real_"):
        return "real_prefix_unverified"
    if value.startswith(("synth_", "synthetic_")):
        return "synthetic_prefix_unverified"
    if not value:
        return "missing"
    return "other_prefix_unverified"


def taxonomy_label_preview(intent):
    """Map only explicit source intent names to SOUL's three-class vocabulary."""
    value = str(intent or "").strip().casefold()
    if value == "legitimate / benign":
        return "legitimate"
    if value == "general spam / telemarketing":
        return "spam"
    if value in SCAM_INTENTS:
        return "scam"
    return "needs_review"


def prepare_records(split_records):
    """Preserve source labels/provenance and redact text before local output."""
    rows = []
    seen_ids = set()

    for source_split, source_index, source_row in split_records:
        if not isinstance(source_row, dict):
            raise ValueError("A ScamShield record is not a dictionary.")

        text = str(source_row.get("text") or "").strip()
        if not text:
            raise ValueError(f"Blank message text in split {source_split!r}.")
        if len(text) > 5000:
            raise ValueError("A message exceeds the 5,000-character limit.")

        label = normalise_binary_label(source_row.get("is_scam"))
        language = str(source_row.get("language") or "").strip().casefold()
        source = str(source_row.get("source_dataset") or "").strip()
        intent = str(source_row.get("head2_scam_intent") or "").strip().casefold()
        split_group = str(source_row.get("split_group") or "").strip()
        source_id = str(source_row.get("id") or "").strip()

        if not language:
            language = "unknown"
        if not source:
            source = "unknown"

        record_id = f"SCAMSHIELD_{source_split}_{source_index:07d}"
        if record_id in seen_ids:
            raise ValueError("Generated local record ID collision.")
        seen_ids.add(record_id)

        flags = detect_patterns(text)
        masked_text = neutralize_spreadsheet_formula(mask_candidates(text))
        residual = detect_patterns(masked_text)

        row = {
            "record_id": record_id,
            "source_id": source_id,
            "text": masked_text,
            "source_dataset": source,
            "language": language,
            "source_split": str(source_split).casefold(),
            "source_label_is_scam": label,
            "source_scam_intent": intent or "missing",
            "source_split_group": split_group,
            "content_sha256": sha256_text(text),
            "masked_text_sha256": sha256_text(masked_text),
            "script_profile": script_profile(text),
            "source_type_hint": source_type_hint(source),
            "record_id_prefix_hint": record_id_prefix_hint(source_id),
            "taxonomy_label_preview": taxonomy_label_preview(intent),
            "has_email_upi_candidate": int(bool(flags["email_upi"])),
            "has_url_domain_candidate": int(bool(flags["url_domain"])),
            "has_phone_long_number_candidate": int(bool(flags["phone_long_number"])),
            "has_twelve_digit_candidate": int(bool(flags["twelve_digit"])),
            "has_pan_like_candidate": int(bool(flags["pan_like"])),
            "has_residual_candidate_after_mask": int(any(residual.values())),
        }
        for name in PRIVACY_FIELDS:
            row[f"residual_{name}_candidate"] = int(bool(residual[name]))

        metadata = source_row.get("metadata")
        social = source_row.get("head1_social_engineering")
        for name in METADATA_FLAGS:
            row[f"metadata_{name}"] = safe_flag(metadata, name)
        for name in SOCIAL_FLAGS:
            row[f"social_{name}"] = safe_flag(social, name)

        rows.append(row)

    if not rows:
        raise ValueError("No ScamShield records were loaded.")
    return rows


def audit_records(rows):
    """Produce aggregate-only source, label-intent, split and privacy counts."""
    labels = Counter()
    languages = Counter()
    language_labels = defaultdict(Counter)
    sources = Counter()
    source_labels = defaultdict(Counter)
    splits = Counter()
    intents = Counter()
    intent_by_label = defaultdict(Counter)
    scripts = Counter()
    source_types = Counter()
    id_prefixes = Counter()
    taxonomy_preview = Counter()
    source_language_labels = defaultdict(Counter)
    source_language_class_labels = defaultdict(Counter)
    source_intents = defaultdict(Counter)
    source_intent_class_labels = defaultdict(Counter)
    source_id_prefix_counts = defaultdict(Counter)
    residual_by_source = defaultdict(Counter)
    residual_by_language = defaultdict(Counter)
    residual_patterns = Counter()
    privacy = Counter()
    metadata = Counter()
    social = Counter()
    raw_groups = defaultdict(list)
    masked_groups = defaultdict(list)
    split_groups = defaultdict(list)
    source_split_groups = defaultdict(list)
    group_counts_by_source = defaultdict(Counter)

    for row in rows:
        label = row["source_label_is_scam"]
        language = row["language"]
        source = row["source_dataset"]
        split = row["source_split"]
        intent = row["source_scam_intent"]

        labels[str(label)] += 1
        languages[language] += 1
        language_labels[language][str(label)] += 1
        sources[source] += 1
        source_labels[source][str(label)] += 1
        splits[split] += 1
        intents[intent] += 1
        intent_by_label[str(label)][intent] += 1
        scripts[row["script_profile"]] += 1
        source_types[row["source_type_hint"]] += 1
        id_prefixes[row["record_id_prefix_hint"]] += 1
        taxonomy_preview[row["taxonomy_label_preview"]] += 1
        source_language_labels[source][language] += 1
        source_language_class_labels[(source, language)][str(label)] += 1
        source_intents[source][intent] += 1
        source_intent_class_labels[(source, str(label))][intent] += 1
        source_id_prefix_counts[source][row["record_id_prefix_hint"]] += 1

        raw_groups[row["content_sha256"]].append(row)
        masked_groups[row["masked_text_sha256"]].append(row)
        if row["source_split_group"]:
            split_groups[row["source_split_group"]].append(row)
            source_split_groups[
                (row["source_dataset"], row["source_split_group"])
            ].append(row)
            group_counts_by_source[source][row["source_split_group"]] += 1

        for name in PRIVACY_FIELDS:
            if row[f"has_{name}_candidate"]:
                privacy[name] += 1
        if any(row[f"has_{name}_candidate"] for name in PRIVACY_FIELDS):
            privacy["rows_with_any_candidate"] += 1
        if row["has_residual_candidate_after_mask"]:
            privacy["rows_with_residual_candidate_after_mask"] += 1
            residual_by_source[source]["rows"] += 1
            residual_by_language[language]["rows"] += 1
        for name in PRIVACY_FIELDS:
            if row[f"residual_{name}_candidate"]:
                residual_patterns[name] += 1
                residual_by_source[source][name] += 1
                residual_by_language[language][name] += 1

        for name in METADATA_FLAGS:
            metadata[name] += row[f"metadata_{name}"]
        for name in SOCIAL_FLAGS:
            social[name] += row[f"social_{name}"]

    def duplicate_summary(groups):
        repeated = [members for members in groups.values() if len(members) > 1]
        return {
            "duplicate_groups": len(repeated),
            "rows_in_duplicate_groups": sum(len(members) for members in repeated),
            "groups_crossing_publisher_splits": sum(
                len({row["source_split"] for row in members}) > 1
                for members in repeated
            ),
            "groups_with_conflicting_is_scam_labels": sum(
                len({row["source_label_is_scam"] for row in members}) > 1
                for members in repeated
            ),
            "groups_spanning_source_datasets": sum(
                len({row["source_dataset"] for row in members}) > 1
                for members in repeated
            ),
            "rows_in_groups_spanning_source_datasets": sum(
                len(members)
                for members in repeated
                if len({row["source_dataset"] for row in members}) > 1
            ),
            "cross_source_groups_with_conflicting_is_scam_labels": sum(
                len({row["source_dataset"] for row in members}) > 1
                and len({row["source_label_is_scam"] for row in members}) > 1
                for members in repeated
            ),
        }

    repeated_split_groups = [
        members for members in split_groups.values() if len(members) > 1
    ]
    repeated_source_groups = [
        members for members in source_split_groups.values() if len(members) > 1
    ]
    positive_general_spam = intent_by_label["1"].get(
        "general spam / telemarketing", 0
    )
    positive_benign = intent_by_label["1"].get(
        "legitimate / benign", 0
    )
    source_group_cardinality = {}
    for source, group_counts in sorted(group_counts_by_source.items()):
        sizes = list(group_counts.values())
        source_group_cardinality[source] = {
            "rows_with_group_id": int(sum(sizes)),
            "unique_group_ids": len(group_counts),
            "repeated_group_ids": sum(size > 1 for size in sizes),
            "largest_group_size": max(sizes, default=0),
            "groups_with_at_least_1000_rows": sum(size >= 1000 for size in sizes),
        }

    return {
        "total_records": len(rows),
        "label_counts_is_scam": dict(sorted(labels.items())),
        "language_counts": dict(sorted(languages.items())),
        "language_label_counts": {
            key: dict(sorted(value.items()))
            for key, value in sorted(language_labels.items())
        },
        "source_dataset_counts": dict(sorted(sources.items())),
        "source_dataset_label_counts": {
            key: dict(sorted(value.items()))
            for key, value in sorted(source_labels.items())
        },
        "publisher_split_counts": dict(sorted(splits.items())),
        "source_scam_intent_counts": dict(sorted(intents.items())),
        "source_intent_counts_by_is_scam": {
            key: dict(sorted(value.items()))
            for key, value in sorted(intent_by_label.items())
        },
        "script_profile_counts": dict(sorted(scripts.items())),
        "source_type_name_hints": dict(sorted(source_types.items())),
        "record_id_prefix_hints_unverified": dict(sorted(id_prefixes.items())),
        "taxonomy_three_class_preview_unverified": dict(sorted(taxonomy_preview.items())),
        "source_language_counts": {
            source: dict(sorted(counts.items()))
            for source, counts in sorted(source_language_labels.items())
        },
        "source_language_class_counts": {
            f"{source} | {language}": dict(sorted(counts.items()))
            for (source, language), counts in sorted(source_language_class_labels.items())
        },
        "source_intent_counts": {
            source: dict(sorted(counts.items()))
            for source, counts in sorted(source_intents.items())
        },
        "source_intent_counts_by_is_scam": {
            f"{source} | is_scam={label}": dict(sorted(counts.items()))
            for (source, label), counts in sorted(source_intent_class_labels.items())
        },
        "source_record_id_prefix_hints_unverified": {
            source: dict(sorted(counts.items()))
            for source, counts in sorted(source_id_prefix_counts.items())
        },
        "residual_pattern_counts_after_mask": dict(sorted(residual_patterns.items())),
        "residual_rows_by_source": {
            source: dict(sorted(counts.items()))
            for source, counts in sorted(residual_by_source.items())
        },
        "residual_rows_by_language": {
            language: dict(sorted(counts.items()))
            for language, counts in sorted(residual_by_language.items())
        },
        "raw_text_duplicate_audit": duplicate_summary(raw_groups),
        "masked_text_duplicate_audit": duplicate_summary(masked_groups),
        "publisher_split_group_cardinality_by_source": source_group_cardinality,
        "publisher_split_group_audit": {
            "nonempty_group_ids": len(split_groups),
            "repeated_groups": len(repeated_split_groups),
            "repeated_groups_crossing_publisher_splits": sum(
                len({row["source_split"] for row in members}) > 1
                for members in repeated_split_groups
            ),
            "repeated_groups_with_mixed_is_scam_labels": sum(
                len({row["source_label_is_scam"] for row in members}) > 1
                for members in repeated_split_groups
            ),
            "source_scoped_repeated_groups": len(repeated_source_groups),
            "source_scoped_groups_crossing_publisher_splits": sum(
                len({row["source_split"] for row in members}) > 1
                for members in repeated_source_groups
            ),
        },
        "privacy_candidate_counts": dict(sorted(privacy.items())),
        "source_metadata_flag_counts": dict(sorted(metadata.items())),
        "source_social_signal_counts": dict(sorted(social.items())),
        "positive_general_spam_telemarketing_rows": int(positive_general_spam),
        "positive_legitimate_benign_intent_rows": int(positive_benign),
        "model_trained": False,
        "publisher_split_approved_for_evaluation": False,
        "source_license_review_complete": False,
        "source_labels_reinterpreted": False,
        "row_level_message_text_printed": False,
    }


def write_outputs(rows, summary, output_csv=OUTPUT_CSV, output_json=OUTPUT_JSON):
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "dataset_id": DATASET_ID,
        "audit_created_at_utc": datetime.now(timezone.utc).isoformat(),
        "declared_license": "MIT (dataset-card metadata; upstream rights not verified)",
        "source_type": "mixed / source-specific provenance pending",
        "task": "source-defined binary is_scam classification; label semantics require audit",
        "publisher_split_policy": (
            "Original train/val/test are retained as provenance only. "
            "SOUL has not approved these as campaign-independent partitions."
        ),
        "privacy_note": (
            "Regex-based masking is candidate redaction only and does not prove "
            "complete anonymisation."
        ),
        "summary": summary,
    }
    with output_json.open("w", encoding="utf-8") as output:
        json.dump(manifest, output, indent=2, ensure_ascii=False)


def load_huggingface_candidate(loader=None):
    if loader is None:
        try:
            from datasets import load_dataset
        except ImportError as error:
            raise SystemExit(
                "Optional package datasets is required. Install it with "
                "python -m pip install datasets."
            ) from error
        loader = load_dataset

    dataset = loader(DATASET_ID, trust_remote_code=False)
    if not hasattr(dataset, "keys"):
        raise ValueError("Hugging Face loader did not return a split mapping.")

    available = {str(name).casefold() for name in dataset.keys()}
    if not available or not available.issubset(KNOWN_SPLITS):
        raise ValueError(
            "Unexpected publisher split names: " + ", ".join(sorted(available))
        )
    has_validation = "val" in available or "validation" in available
    missing_partitions = []
    if "train" not in available:
        missing_partitions.append("train")
    if not has_validation:
        missing_partitions.append("val/validation")
    if "test" not in available:
        missing_partitions.append("test")
    if missing_partitions:
        raise ValueError(
            "Publisher dataset is missing required splits: "
            + ", ".join(missing_partitions)
        )

    required = {
        "id",
        "text",
        "language",
        "source_dataset",
        "is_scam",
        "head2_scam_intent",
        "split_group",
        "metadata",
        "head1_social_engineering",
    }
    split_records = []
    for split_name in dataset.keys():
        split = dataset[split_name]
        columns = set(getattr(split, "column_names", []) or [])
        missing = required - columns
        if missing:
            raise ValueError(
                f"Split {split_name!r} is missing columns: "
                + ", ".join(sorted(missing))
            )
        for index, row in enumerate(split):
            split_records.append((str(split_name).casefold(), index, row))

    return split_records


def print_summary(summary):
    print("SOUL — ScamShield multilingual candidate audit")
    print("Dataset:", DATASET_ID)
    print("Prepared and masked rows:", summary["total_records"])
    print("Model trained: no")
    print("Publisher split accepted as independent evaluation: no")

    print("\nSource labels (0=source says not scam, 1=source says scam):")
    for label, count in summary["label_counts_is_scam"].items():
        print(f"  {label}: {count}")

    print("\nLanguage tags:")
    for language, count in summary["language_counts"].items():
        print(f"  {language}: {count}")

    print("\nSource datasets:")
    for source, count in summary["source_dataset_counts"].items():
        print(f"  {source}: {count}")

    print("\nPublisher splits:")
    for split, count in summary["publisher_split_counts"].items():
        print(f"  {split}: {count}")

    print("\nSource scam-intent taxonomy:")
    for intent, count in summary["source_scam_intent_counts"].items():
        print(f"  {intent}: {count}")
    print("  Intent counts by source binary label:")
    for label, counts in summary["source_intent_counts_by_is_scam"].items():
        print(f"    is_scam={label}: {counts}")
    print("  Three-class taxonomy preview (NOT approved training labels):",
          summary["taxonomy_three_class_preview_unverified"])
    print("  Unverified source ID prefix hints:",
          summary["record_id_prefix_hints_unverified"])
    print(
        "Positive rows labelled General Spam / Telemarketing:",
        summary["positive_general_spam_telemarketing_rows"],
    )
    print(
        "Positive rows labelled Legitimate / Benign:",
        summary["positive_legitimate_benign_intent_rows"],
    )

    print("\nDuplicate audit:")
    for name in ("raw_text_duplicate_audit", "masked_text_duplicate_audit"):
        values = summary[name]
        print(
            f"  {name}: groups={values['duplicate_groups']}, "
            f"cross-split={values['groups_crossing_publisher_splits']}, "
            f"mixed-label={values['groups_with_conflicting_is_scam_labels']}, "
            f"cross-source={values['groups_spanning_source_datasets']}, "
            f"cross-source mixed-label="
            f"{values['cross_source_groups_with_conflicting_is_scam_labels']}"
        )
    print(
        "  Publisher split groups crossing splits:",
        summary["publisher_split_group_audit"][
            "repeated_groups_crossing_publisher_splits"
        ],
    )
    print("  Split-group cardinality by source:")
    for source, values in summary["publisher_split_group_cardinality_by_source"].items():
        print(
            f"    {source}: {values['unique_group_ids']} unique IDs / "
            f"{values['rows_with_group_id']} rows; "
            f"largest group={values['largest_group_size']}"
        )

    print("\nPrivacy-pattern candidates:")
    for name, count in summary["privacy_candidate_counts"].items():
        print(f"  {name}: {count}")
    print("  Residual pattern matches after masking:",
          summary["residual_pattern_counts_after_mask"])
    print("  Residual rows by source:",
          summary["residual_rows_by_source"])
    print("  Residual rows by language:",
          summary["residual_rows_by_language"])

    print("\nOutputs:")
    print("  Masked row-level CSV:", OUTPUT_CSV)
    print("  Aggregate JSON:", OUTPUT_JSON)
    print(
        "\nSource labels and intent taxonomy were preserved. "
        "No model trained; no messages printed; no three-class mapping performed."
    )


def main():
    try:
        records = load_huggingface_candidate()
        rows = prepare_records(records)
        summary = audit_records(rows)
        write_outputs(rows, summary)
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"ScamShield candidate audit failed: {error}") from error

    print_summary(summary)


if __name__ == "__main__":
    main()
