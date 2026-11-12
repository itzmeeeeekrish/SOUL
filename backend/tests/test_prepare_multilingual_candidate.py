"""Tests for safe preparation and group-level splitting of multilingual SMS."""

import hashlib
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from prepare_multilingual_candidate import (
    aggregate_summary,
    create_grouped_splits,
    prepare_rows,
    validate_grouped_splits,
)


def row(record_id, text, label="ham", language="english", split="train"):
    normalised = " ".join(text.casefold().split())
    text_hash = hashlib.sha256(normalised.encode("utf-8")).hexdigest()
    return {
        "record_id": record_id,
        "text": text,
        "model_text_sha256": text_hash,
        "group_id": f"TESTG_{text_hash[:16]}",
        "source_dataset": "test/source",
        "source_split": split,
        "source_label": label,
        "label_task": "scam_vs_ham",
        "language": language,
        "script_profile": "latin_only",
        "source_type": "synthetic",
        "declared_license": "MIT",
        "content_sha256": record_id,
        "has_email_upi_candidate": "0",
        "has_url_domain_candidate": "0",
        "has_phone_long_number_candidate": "0",
        "has_twelve_digit_candidate": "0",
        "has_pan_like_candidate": "0",
    }


def balanced_rows(groups_per_stratum=20):
    rows = []
    index = 0
    for language in ("english", "hindi"):
        for label in ("ham", "scam"):
            for item in range(groups_per_stratum):
                index += 1
                rows.append(
                    row(
                        f"R{index}",
                        f"{language} {label} unique template {item}",
                        label,
                        language,
                    )
                )
    return rows


def test_prepare_rows_masks_phone_and_url_candidates():
    rows, quarantine, stats = prepare_rows(
        [
            row(
                "R1",
                "Call +91 98765 43210 or visit https://example.com",
                "scam",
            )
        ]
    )

    assert quarantine == []
    assert len(rows) == 1
    assert any(
        marker in rows[0]["text"]
        for marker in ("[LONG_NUMBER]", "[12_DIGIT_NUMBER]")
    )
    assert "[URL]" in rows[0]["text"]
    assert rows[0]["has_phone_long_number_candidate"] == 1
    assert rows[0]["has_url_domain_candidate"] == 1
    assert stats["rows_with_residual_candidate_after_mask"] == 0


def test_prepare_rows_collapses_same_masked_text_same_language_and_label():
    rows, quarantine, stats = prepare_rows(
        [
            row("R1", "Your account +91 98765 43210", "ham", "english", "train"),
            row("R2", "Your account +91 91234 56780", "ham", "english", "test"),
        ]
    )

    assert quarantine == []
    assert len(rows) == 1
    assert rows[0]["source_occurrences"] == 2
    assert rows[0]["source_splits"] == "test;train"
    assert stats["same_language_masked_duplicate_groups_collapsed"] == 1


def test_prepare_rows_quarantines_conflicting_masked_text_labels():
    rows, quarantine, stats = prepare_rows(
        [
            row("R1", "Claim prize +91 98765 43210", "ham"),
            row("R2", "Claim prize +91 91234 56780", "scam"),
        ]
    )

    assert rows == []
    assert len(quarantine) == 1
    assert quarantine[0]["reason"] == "same_masked_text_conflicting_binary_labels"
    assert stats["masked_text_conflict_rows"] == 2


def test_prepare_rows_keeps_same_masked_text_with_distinct_language_tags():
    rows, quarantine, stats = prepare_rows(
        [
            row("R1", "Aapka account", "ham", "hinglish"),
            row("R2", "Aapka account", "ham", "english", "test"),
        ]
    )

    assert quarantine == []
    assert len(rows) == 2
    assert {item["group_id"] for item in rows} == {rows[0]["group_id"]}
    assert stats["same_masked_text_multiple_language_tags"] == 1


def test_create_grouped_splits_keeps_group_ids_in_one_partition():
    rows = balanced_rows()
    splits = create_grouped_splits(rows, seed=42)

    assert set(splits) == {"train", "validation", "test"}
    assert all(splits[name] for name in splits)
    assert validate_grouped_splits(splits) is True

    group_to_split = {}
    for split_name, members in splits.items():
        for item in members:
            group_id = item["group_id"]
            assert group_id not in group_to_split or group_to_split[group_id] == split_name
            group_to_split[group_id] = split_name


def test_grouped_split_is_deterministic():
    rows = balanced_rows()
    first = create_grouped_splits(rows, seed=99)
    second = create_grouped_splits(rows, seed=99)

    first_ids = {
        name: [item["record_id"] for item in values]
        for name, values in first.items()
    }
    second_ids = {
        name: [item["record_id"] for item in values]
        for name, values in second.items()
    }
    assert first_ids == second_ids


def test_validator_rejects_identical_text_hash_in_multiple_splits():
    bad = {
        "train": [row("R1", "message", "ham") | {"model_text_sha256": "same", "group_id": "G1"}],
        "validation": [row("R2", "message", "ham") | {"model_text_sha256": "same", "group_id": "G2"}],
        "test": [],
    }

    with pytest.raises(ValueError, match="Identical masked model text"):
        validate_grouped_splits(bad)


def test_grouped_summary_reports_no_baseline_mutation():
    rows = balanced_rows()
    splits = create_grouped_splits(rows)
    summary = aggregate_summary(rows, [], splits, {"source_rows": len(rows)})

    assert summary["model_trained"] is False
    assert summary["historical_baseline_modified"] is False
    assert summary["publisher_split_used_for_evaluation"] is False
    assert summary["group_leakage_check"] == "passed"


def test_prepare_rows_rejects_blank_text():
    with pytest.raises(ValueError, match="blank message"):
        prepare_rows([row("R1", "   ")])


def test_prepare_rows_rejects_unknown_label():
    with pytest.raises(ValueError, match="Unsupported candidate label"):
        prepare_rows([row("R1", "Some message", "spam")])


def test_prepare_rows_rejects_duplicate_input_ids():
    with pytest.raises(ValueError, match="duplicate record_id"):
        prepare_rows([row("R1", "one"), row("R1", "two")])


def test_grouped_split_requires_at_least_ten_unique_groups():
    with pytest.raises(ValueError, match="10 unique masked-text groups"):
        create_grouped_splits(balanced_rows(groups_per_stratum=1))
