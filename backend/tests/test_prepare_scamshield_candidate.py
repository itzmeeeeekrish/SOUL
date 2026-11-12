import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from prepare_scamshield_candidate import (
    CANDIDATE_COLUMNS,
    QUARANTINE_COLUMNS,
    classify_group,
    curate_rows,
    load_audit_rows,
    sha256_text,
    write_curation_outputs,
)


def make_row(
    record_id="one",
    text="A normal message",
    source="UCI_SMS_Spam",
    language="english",
    source_split="train",
    binary="0",
    intent="legitimate / benign",
    taxonomy="legitimate",
    residual="0",
    split_group="source_bucket",
):
    return {
        "record_id": record_id,
        "source_id": record_id,
        "text": text,
        "source_dataset": source,
        "language": language,
        "source_split": source_split,
        "source_label_is_scam": binary,
        "source_scam_intent": intent,
        "source_split_group": split_group,
        "content_sha256": hashlib.sha256(text.casefold().encode()).hexdigest(),
        "masked_text_sha256": sha256_text(text),
        "script_profile": "latin",
        "source_type_hint": "non_synthetic_named_source_unverified",
        "record_id_prefix_hint": "real_prefix_unverified",
        "taxonomy_label_preview": taxonomy,
        "has_residual_candidate_after_mask": residual,
        "residual_email_upi_candidate": residual,
        "residual_url_domain_candidate": "0",
        "residual_phone_long_number_candidate": "0",
        "residual_twelve_digit_candidate": "0",
        "residual_pan_like_candidate": "0",
        "has_email_upi_candidate": "0",
        "has_url_domain_candidate": "0",
        "has_phone_long_number_candidate": "0",
        "has_twelve_digit_candidate": "0",
        "has_pan_like_candidate": "0",
        "metadata_has_url": "0",
        "metadata_has_phone": "0",
        "metadata_has_otp": "0",
        "metadata_has_upi": "0",
        "metadata_has_amount": "0",
        "social_urgency": "0",
        "social_fear": "0",
        "social_authority_impersonation": "0",
        "social_reward_bait": "0",
        "social_financial_pressure": "0",
    }


def test_same_masked_text_from_two_sources_collapses_and_preserves_provenance():
    rows = [
        make_row(record_id="a", source="UCI_SMS_Spam", source_split="train"),
        make_row(record_id="b", source="Indian_Telecom_SMS", source_split="test"),
    ]

    candidates, review, quarantine, summary = curate_rows(rows)

    assert len(candidates) == 1
    assert review == []
    assert quarantine == []
    row = candidates[0]
    assert row["label"] == "legitimate"
    assert row["occurrence_count"] == 2
    assert json.loads(row["source_datasets_json"]) == [
        "Indian_Telecom_SMS",
        "UCI_SMS_Spam",
    ]
    assert row["cross_source_duplicate_group"] == 1
    assert row["cross_publisher_split_duplicate_group"] == 1
    assert summary["duplicate_occurrences_collapsed_in_candidates"] == 1


def test_residual_privacy_candidate_quarantines_the_whole_text_group():
    rows = [
        make_row(record_id="a", residual="1"),
        make_row(record_id="b", source="Indian_Telecom_SMS"),
    ]

    candidates, review, quarantine, summary = curate_rows(rows)

    assert candidates == []
    assert review == []
    assert len(quarantine) == 2
    assert "residual_privacy_pattern_after_mask" in quarantine[0]["curation_reasons"]
    assert summary["quarantined_source_rows"] == 2


def test_conflicting_source_binary_labels_quarantine_all_occurrences():
    rows = [
        make_row(record_id="a", binary="0", taxonomy="legitimate"),
        make_row(
            record_id="b",
            source="Indian_Telecom_SMS",
            binary="1",
            intent="fake kyc",
            taxonomy="scam",
        ),
    ]

    candidates, review, quarantine, _ = curate_rows(rows)

    assert candidates == []
    assert review == []
    assert len(quarantine) == 2
    assert "conflicting_source_binary_labels" in quarantine[0]["curation_reasons"]


def test_conflicting_three_class_intents_are_quarantined_even_when_binary_is_same():
    rows = [
        make_row(record_id="a", binary="1", intent="general spam / telemarketing",
                 taxonomy="spam"),
        make_row(record_id="b", source="Indian_Telecom_SMS", binary="1",
                 intent="fake kyc", taxonomy="scam"),
    ]

    candidates, _, quarantine, _ = curate_rows(rows)

    assert candidates == []
    assert len(quarantine) == 2
    assert "conflicting_three_class_taxonomy_labels" in quarantine[0]["curation_reasons"]


def test_binary_and_intent_semantic_mismatch_is_quarantined():
    rows = [
        make_row(binary="0", intent="fake kyc", taxonomy="scam"),
    ]

    candidates, _, quarantine, _ = curate_rows(rows)

    assert candidates == []
    assert len(quarantine) == 1
    assert "source_binary_intent_semantic_mismatch" in quarantine[0]["curation_reasons"]


def test_unmapped_intent_goes_to_needs_review_not_training_candidate():
    rows = [
        make_row(intent="unknown intent", taxonomy="needs_review"),
    ]

    candidates, review, quarantine, _ = curate_rows(rows)

    assert candidates == []
    assert len(review) == 1
    assert review[0]["label"] == "needs_review"
    assert quarantine == []


def test_language_tag_conflict_goes_to_review():
    rows = [
        make_row(record_id="a", language="english"),
        make_row(record_id="b", language="hindi"),
    ]

    candidates, review, quarantine, _ = curate_rows(rows)

    assert candidates == []
    assert len(review) == 1
    assert "conflicting_language_tags" in review[0]["curation_reasons"]
    assert quarantine == []


def test_groups_with_only_source_intent_taxonomy_labels_get_provisional_silver_label():
    rows = [
        make_row(binary="1", intent="fake kyc", taxonomy="scam"),
        make_row(
            record_id="two",
            text="Promotional offer message",
            binary="1",
            intent="general spam / telemarketing",
            taxonomy="spam",
        ),
        make_row(
            record_id="three",
            text="Your appointment is confirmed",
            binary="0",
            taxonomy="legitimate",
        ),
    ]

    candidates, review, quarantine, summary = curate_rows(rows)

    assert len(candidates) == 3
    assert {row["label"] for row in candidates} == {
        "legitimate", "spam", "scam"
    }
    assert review == []
    assert quarantine == []
    assert summary["training_labels_are_provisional_silver"] is True
    assert summary["human_verified_ground_truth"] is False
    assert summary["model_trained"] is False


def test_masked_hash_mismatch_is_rejected_before_curation(tmp_path):
    row = make_row()
    row["masked_text_sha256"] = "0" * 64
    path = tmp_path / "bad.csv"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)

    with pytest.raises(ValueError, match="hash mismatch"):
        load_audit_rows(path)


def test_missing_audit_file_explains_required_previous_step(tmp_path):
    with pytest.raises(FileNotFoundError, match="Run data/audit_scamshield_candidate.py"):
        load_audit_rows(tmp_path / "missing.csv")


def test_output_files_are_created_with_explicit_private_preview_status(tmp_path):
    rows = [
        make_row(binary="1", intent="fake kyc", taxonomy="scam"),
        make_row(
            record_id="review",
            text="Unmapped content",
            binary="1",
            intent="other",
            taxonomy="needs_review",
        ),
        make_row(
            record_id="private",
            text="Residual identifier",
            residual="1",
        ),
    ]
    candidates, review, quarantine, summary = curate_rows(rows)
    outputs = write_curation_outputs(
        candidates, review, quarantine, summary, tmp_path
    )

    with outputs["candidate"].open("r", encoding="utf-8-sig", newline="") as source:
        candidate_rows = list(csv.DictReader(source))
    with outputs["review"].open("r", encoding="utf-8-sig", newline="") as source:
        review_rows = list(csv.DictReader(source))
    with outputs["quarantine"].open("r", encoding="utf-8-sig", newline="") as source:
        quarantine_rows = list(csv.DictReader(source))
    manifest = json.loads(outputs["summary"].read_text(encoding="utf-8"))

    assert len(candidate_rows) == 1
    assert set(candidate_rows[0]) == set(CANDIDATE_COLUMNS)
    assert len(review_rows) == 1
    assert len(quarantine_rows) == 1
    assert set(quarantine_rows[0]) == set(QUARANTINE_COLUMNS)
    assert manifest["summary"]["model_trained"] is False
    assert "not independently human-verified" in manifest["label_status"]


def test_empty_input_to_curate_is_rejected_by_loader(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("record_id,text\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_audit_rows(path)


def test_multiple_same_class_occurrences_are_collapsed_without_losing_intents():
    rows = [
        make_row(record_id="a", binary="1", intent="fake kyc", taxonomy="scam"),
        make_row(
            record_id="b",
            source="Synthetic_Tier_C",
            binary="1",
            intent="upi fraud",
            taxonomy="scam",
        ),
    ]

    candidates, review, quarantine, _ = curate_rows(rows)

    assert len(candidates) == 1
    assert json.loads(candidates[0]["source_intents_json"]) == [
        "fake kyc", "upi fraud"
    ]
    assert candidates[0]["occurrence_count"] == 2
    assert review == []
    assert quarantine == []


def test_grouping_by_hash_checks_normalised_text_consistency():
    first = make_row(record_id="a", text="Same  text")
    second = make_row(record_id="b", text="Same text")
    second["masked_text_sha256"] = first["masked_text_sha256"]

    action, reasons = classify_group([first, second])

    assert action == "candidate"
    assert reasons == []


def test_summary_does_not_treat_split_group_as_campaign_or_make_splits():
    rows = [
        make_row(split_group="one_source_bucket"),
        make_row(
            record_id="two",
            text="Another unique message",
            split_group="one_source_bucket",
        ),
    ]

    candidates, review, quarantine, summary = curate_rows(rows)

    assert len(candidates) == 2
    assert summary["train_validation_test_split_created"] is False
    assert summary["model_trained"] is False
