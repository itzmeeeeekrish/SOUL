"""Aggregate-only audit/importer for the 14-language synthetic SMS candidate.

This script downloads the Hugging Face dataset to the local Hugging Face cache,
then writes a private, provenance-preserving CSV and aggregate JSON report.
It does not train a model, overwrite the Mendeley derivative, or reuse the
publisher's split as SOUL's evaluation split.

Optional dependency:
    python -m pip install datasets

Run from the repository root:
    python data/audit_multilingual_candidate.py

All row-level output is written beneath Git-ignored data/private/.
"""

import csv
import hashlib
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from audit_mendeley_privacy import detect_patterns
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from audit_mendeley_privacy import detect_patterns


DATASET_ID = "anmolshrivastav/scam_ham_india_14_languages"
DATASET_DIRECTORY = (
    Path(__file__).resolve().parent
    / "private"
    / "multilingual_candidates"
)
OUTPUT_CSV = DATASET_DIRECTORY / "anmolshrivastav_14lang_candidate_audit.csv"
OUTPUT_JSON = DATASET_DIRECTORY / "anmolshrivastav_14lang_candidate_summary.json"

EXPECTED_SPLITS = ("train", "test")
OUTPUT_COLUMNS = [
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
    "content_group_id",
    "has_email_upi_candidate",
    "has_url_domain_candidate",
    "has_phone_long_number_candidate",
    "has_twelve_digit_candidate",
    "has_pan_like_candidate",
]


def normalise_text(text):
    """Normalise only whitespace and case for exact duplicate grouping."""
    return " ".join((text or "").casefold().split())


def normalise_label(value):
    """Map the documented binary source labels without changing task semantics."""
    if isinstance(value, bool):
        raise ValueError("Boolean labels are not supported.")

    if isinstance(value, int):
        value = str(value)
    label = str(value or "").strip().casefold()

    mapping = {
        "0": "ham",
        "ham": "ham",
        "legitimate": "ham",
        "safe": "ham",
        "1": "scam",
        "scam": "scam",
        "fraud": "scam",
    }
    if label not in mapping:
        raise ValueError(f"Unsupported source label: {label!r}")
    return mapping[label]


def script_profile(text):
    """Return a coarse Unicode-script profile, not a language prediction."""
    scripts = set()

    for character in text or "":
        if not character.isalpha():
            continue
        name = unicodedata.name(character, "")
        if "LATIN" in name:
            scripts.add("latin")
        elif "DEVANAGARI" in name:
            scripts.add("devanagari")
        elif "BENGALI" in name or "ASSAMESE" in name:
            scripts.add("bengali_assamese")
        elif "GURMUKHI" in name:
            scripts.add("gurmukhi")
        elif "GUJARATI" in name:
            scripts.add("gujarati")
        elif "ORIYA" in name or "ODIA" in name:
            scripts.add("odia")
        elif "TAMIL" in name:
            scripts.add("tamil")
        elif "TELUGU" in name:
            scripts.add("telugu")
        elif "KANNADA" in name:
            scripts.add("kannada")
        elif "MALAYALAM" in name:
            scripts.add("malayalam")
        elif "ARABIC" in name:
            scripts.add("arabic")
        else:
            scripts.add("other_non_latin")

    if not scripts:
        return "no_letters"
    if scripts == {"latin"}:
        return "latin_only"
    if len(scripts) == 1:
        return next(iter(scripts))
    if "latin" in scripts:
        return "mixed_latin_non_latin"
    return "mixed_non_latin"


def prepare_candidate_rows(split_records):
    """Convert source rows to a consistent local audit schema."""
    prepared = []
    seen_record_ids = set()

    for source_split, source_index, source_row in split_records:
        if not isinstance(source_row, dict):
            raise ValueError("A dataset row is not a dictionary.")

        text = str(source_row.get("text") or "").strip()
        language = str(source_row.get("language") or "").strip().casefold()
        if not text:
            raise ValueError(f"Blank text in source split {source_split!r}.")
        if len(text) > 5000:
            raise ValueError("A message exceeds the 5,000-character safety limit.")
        if not language:
            raise ValueError("A source language tag is blank.")

        label = normalise_label(source_row.get("label"))
        content_hash = hashlib.sha256(
            normalise_text(text).encode("utf-8")
        ).hexdigest()
        record_id = f"HF14_{source_split}_{source_index:06d}"
        if record_id in seen_record_ids:
            raise ValueError("A generated local record ID is duplicated.")
        seen_record_ids.add(record_id)

        flags = detect_patterns(text)

        prepared.append(
            {
                "record_id": record_id,
                "text": text,
                "source_dataset": DATASET_ID,
                "source_split": source_split,
                "source_label": label,
                "label_task": "scam_vs_ham",
                "language": language,
                "script_profile": script_profile(text),
                "source_type": "synthetic",
                "declared_license": "MIT (dataset-card metadata; verify terms)",
                "content_sha256": content_hash,
                "content_group_id": f"HF14G_{content_hash[:16]}",
                "has_email_upi_candidate": int(flags["email_upi"]),
                "has_url_domain_candidate": int(flags["url_domain"]),
                "has_phone_long_number_candidate": int(flags["phone_long_number"]),
                "has_twelve_digit_candidate": int(flags["twelve_digit"]),
                "has_pan_like_candidate": int(flags["pan_like"]),
            }
        )

    if not prepared:
        raise ValueError("No candidate rows were loaded.")
    return prepared


def audit_prepared_rows(rows):
    """Return aggregate-only counts; never return message text or identifiers."""
    labels = Counter()
    languages = Counter()
    language_label_counts = defaultdict(Counter)
    source_splits = Counter()
    scripts = Counter()
    privacy = Counter()
    groups = defaultdict(list)

    for row in rows:
        label = row["source_label"]
        language = row["language"]
        split = row["source_split"]

        labels[label] += 1
        languages[language] += 1
        language_label_counts[language][label] += 1
        source_splits[split] += 1
        scripts[row["script_profile"]] += 1
        groups[row["content_sha256"]].append(row)

        flags = (
            "has_email_upi_candidate",
            "has_url_domain_candidate",
            "has_phone_long_number_candidate",
            "has_twelve_digit_candidate",
            "has_pan_like_candidate",
        )
        matched = [name for name in flags if row[name]]
        for name in matched:
            privacy[name] += 1
        if matched:
            privacy["rows_with_any_candidate"] += 1

    duplicate_groups = 0
    rows_in_duplicate_groups = 0
    cross_split_duplicate_groups = 0
    cross_label_duplicate_groups = 0

    for members in groups.values():
        if len(members) <= 1:
            continue
        duplicate_groups += 1
        rows_in_duplicate_groups += len(members)
        if len({row["source_split"] for row in members}) > 1:
            cross_split_duplicate_groups += 1
        if len({row["source_label"] for row in members}) > 1:
            cross_label_duplicate_groups += 1

    return {
        "total_records": len(rows),
        "label_counts": dict(sorted(labels.items())),
        "language_counts": dict(sorted(languages.items())),
        "language_label_counts": {
            language: dict(sorted(counts.items()))
            for language, counts in sorted(language_label_counts.items())
        },
        "publisher_split_counts": dict(sorted(source_splits.items())),
        "script_profile_counts": dict(sorted(scripts.items())),
        "privacy_candidate_counts": dict(sorted(privacy.items())),
        "unique_normalised_texts": len(groups),
        "duplicate_text_groups": duplicate_groups,
        "records_in_duplicate_text_groups": rows_in_duplicate_groups,
        "duplicate_groups_crossing_publisher_splits": cross_split_duplicate_groups,
        "duplicate_groups_with_conflicting_labels": cross_label_duplicate_groups,
    }


def write_audit_outputs(rows, summary, output_csv=OUTPUT_CSV, output_json=OUTPUT_JSON):
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "dataset_id": DATASET_ID,
        "audit_created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_type": "synthetic",
        "declared_license": "MIT (dataset-card metadata; verify terms)",
        "label_task": "scam_vs_ham",
        "publisher_split_policy": (
            "The publisher card describes a stratified 90/10 split. "
            "SOUL has not established group/campaign isolation."
        ),
        "summary": summary,
        "message_text_printed": False,
        "model_trained": False,
        "historical_baseline_modified": False,
        "evaluation_approval": False,
    }
    with output_json.open("w", encoding="utf-8") as destination:
        json.dump(manifest, destination, indent=2, ensure_ascii=False)


def load_huggingface_candidate(loader=None):
    """Download with the optional Hugging Face datasets package."""
    if loader is None:
        try:
            from datasets import load_dataset
        except ImportError as error:
            raise SystemExit(
                "Optional package 'datasets' is required. Install it with "
                "'python -m pip install datasets'."
            ) from error
        loader = load_dataset

    dataset = loader(DATASET_ID, trust_remote_code=False)
    missing = set(EXPECTED_SPLITS) - set(dataset.keys())
    if missing:
        raise ValueError(
            "The Hugging Face dataset is missing expected splits: "
            + ", ".join(sorted(missing))
        )

    split_records = []
    for split_name in EXPECTED_SPLITS:
        split = dataset[split_name]
        for index, row in enumerate(split):
            split_records.append((split_name, index, row))
    return split_records


def print_summary(summary, output_csv=OUTPUT_CSV, output_json=OUTPUT_JSON):
    print("SOUL — multilingual candidate audit (aggregate only)")
    print("Dataset:", DATASET_ID)
    print("Prepared records:", summary["total_records"])

    print("\nSource labels:")
    for label, count in summary["label_counts"].items():
        print(f"  {label}: {count}")

    print("\nLanguage tags:")
    for language, count in summary["language_counts"].items():
        print(f"  {language}: {count}")

    print("\nScript profiles:")
    for profile, count in summary["script_profile_counts"].items():
        print(f"  {profile}: {count}")

    print("\nPublisher split counts:")
    for split, count in summary["publisher_split_counts"].items():
        print(f"  {split}: {count}")

    print("\nDuplicate checks:")
    print("  Unique normalised texts:", summary["unique_normalised_texts"])
    print("  Duplicate text groups:", summary["duplicate_text_groups"])
    print(
        "  Duplicate groups crossing publisher splits:",
        summary["duplicate_groups_crossing_publisher_splits"],
    )
    print(
        "  Duplicate groups with conflicting source labels:",
        summary["duplicate_groups_with_conflicting_labels"],
    )

    print("\nPrivacy-pattern candidates:")
    for name, count in summary["privacy_candidate_counts"].items():
        print(f"  {name}: {count}")

    print("\nOutput CSV:", output_csv)
    print("Aggregate JSON:", output_json)
    print(
        "No model was trained. The publisher split is not approved as SOUL's "
        "independent evaluation split. No message text or row identifiers were printed."
    )


def main():
    try:
        split_records = load_huggingface_candidate()
        rows = prepare_candidate_rows(split_records)
        summary = audit_prepared_rows(rows)
        write_audit_outputs(rows, summary)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(f"Multilingual candidate audit failed: {error}") from error

    print_summary(summary)


if __name__ == "__main__":
    main()
