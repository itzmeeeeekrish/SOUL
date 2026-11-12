import csv
import json
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_scamshield_candidate import (
    DATASET_ID,
    OUTPUT_COLUMNS,
    audit_records,
    load_huggingface_candidate,
    normalise_binary_label,
    prepare_records,
    safe_flag,
    source_type_hint,
    taxonomy_label_preview,
    record_id_prefix_hint,
    write_outputs,
)


def make_source_row(
    record_id="real_1",
    text="Normal message",
    source="UCI_SMS_Spam",
    language="English",
    is_scam=0,
    intent="Legitimate / Benign",
    split_group="group_a",
):
    return {
        "id": record_id,
        "text": text,
        "language": language,
        "source_dataset": source,
        "is_scam": is_scam,
        "head1_social_engineering": {
            "urgency": 0,
            "fear": 0,
            "authority_impersonation": 0,
            "reward_bait": 0,
            "financial_pressure": 0,
        },
        "head2_scam_intent": intent,
        "split_group": split_group,
        "metadata": {
            "has_url": False,
            "has_phone": False,
            "has_otp": False,
            "has_upi": False,
            "has_amount": False,
        },
    }


def test_normalise_binary_label_accepts_documented_values():
    assert normalise_binary_label(False) == 0
    assert normalise_binary_label(True) == 1
    assert normalise_binary_label("ham") == 0
    assert normalise_binary_label("fraud") == 1
    assert normalise_binary_label(0) == 0
    assert normalise_binary_label(1) == 1


def test_normalise_binary_label_rejects_unknown_values():
    with pytest.raises(ValueError, match="Unsupported is_scam"):
        normalise_binary_label("maybe")


def test_safe_flag_accepts_only_boolean_or_binary_integer():
    assert safe_flag({"has_url": True}, "has_url") == 1
    assert safe_flag({"has_url": 0}, "has_url") == 0
    assert safe_flag({"has_url": "yes"}, "has_url") == 0
    assert safe_flag(None, "has_url") == 0


def test_source_type_hint_does_not_claim_unverified_real_provenance():
    assert source_type_hint("Synthetic_Tier_C") == "synthetic_named_source"
    assert (
        source_type_hint("Smishing_Dataset")
        == "non_synthetic_named_source_unverified"
    )
    assert source_type_hint("") == "unknown_source"


def test_prepare_records_preserves_label_intent_and_masks_candidate_text():
    text = "Your account needs review at https://example.com and call 9876543210"
    rows = prepare_records(
        [("train", 0, make_source_row(text=text, is_scam=1,
                                      intent="Fake KYC"))]
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["source_label_is_scam"] == 1
    assert row["source_scam_intent"] == "fake kyc"
    assert row["source_split"] == "train"
    assert row["source_dataset"] == "UCI_SMS_Spam"
    assert row["content_sha256"]
    assert row["masked_text_sha256"]
    assert row["text"] != text
    assert "https://example.com" not in row["text"]
    assert row["has_url_domain_candidate"] == 1
    assert row["source_type_hint"] == "non_synthetic_named_source_unverified"
    assert row["record_id_prefix_hint"] == "real_prefix_unverified"
    assert row["taxonomy_label_preview"] == "scam"


def test_prepare_records_rejects_blank_or_oversized_text_and_invalid_label():
    with pytest.raises(ValueError, match="Blank message text"):
        prepare_records([("train", 0, make_source_row(text=" "))])

    with pytest.raises(ValueError, match="5,000-character"):
        prepare_records([("train", 0, make_source_row(text="x" * 5001))])

    with pytest.raises(ValueError, match="Unsupported is_scam"):
        prepare_records([("train", 0, make_source_row(is_scam=2))])


def test_prepare_records_keeps_generated_record_ids_unique():
    rows = prepare_records(
        [
            ("train", 0, make_source_row(record_id="same")),
            ("test", 0, make_source_row(record_id="same")),
        ]
    )

    assert rows[0]["record_id"] != rows[1]["record_id"]


def test_audit_records_counts_duplicates_groups_and_intent_conflicts():
    source_rows = [
        ("train", 0, make_source_row(
            record_id="a",
            text="Your account is active",
            is_scam=0,
            intent="Legitimate / Benign",
            split_group="shared_group",
        )),
        ("test", 0, make_source_row(
            record_id="b",
            text="Your account is active",
            is_scam=1,
            intent="General Spam / Telemarketing",
            split_group="shared_group",
        )),
        ("train", 1, make_source_row(
            record_id="c",
            text="A different scam message",
            is_scam=1,
            intent="Fake KYC",
            source="Synthetic_Tier_C",
            split_group="synthetic_group",
        )),
    ]
    summary = audit_records(prepare_records(source_rows))

    assert summary["total_records"] == 3
    assert summary["raw_text_duplicate_audit"]["duplicate_groups"] == 1
    assert summary["raw_text_duplicate_audit"]["groups_crossing_publisher_splits"] == 1
    assert summary["raw_text_duplicate_audit"]["groups_with_conflicting_is_scam_labels"] == 1
    assert summary["publisher_split_group_audit"]["repeated_groups_crossing_publisher_splits"] == 1
    assert summary["positive_general_spam_telemarketing_rows"] == 1
    assert summary["source_type_name_hints"]["synthetic_named_source"] == 1
    assert summary["model_trained"] is False


def test_audit_records_keeps_source_label_and_intent_dimensions_separate():
    rows = prepare_records(
        [
            ("train", 0, make_source_row(
                is_scam=1,
                intent="General Spam / Telemarketing",
            )),
            ("train", 1, make_source_row(
                record_id="two",
                text="A second unrelated example",
                is_scam=0,
                intent="Legitimate / Benign",
            )),
        ]
    )
    summary = audit_records(rows)

    assert summary["source_intent_counts_by_is_scam"]["1"][
        "general spam / telemarketing"
    ] == 1
    assert summary["source_intent_counts_by_is_scam"]["0"][
        "legitimate / benign"
    ] == 1
    assert summary["source_labels_reinterpreted"] is False
    assert summary["taxonomy_three_class_preview_unverified"] == {
        "legitimate": 1,
        "spam": 1,
    }


def test_write_outputs_creates_private_row_csv_and_aggregate_json(tmp_path):
    rows = prepare_records(
        [("train", 0, make_source_row(text="A normal test message"))]
    )
    summary = audit_records(rows)
    csv_path = tmp_path / "audit.csv"
    json_path = tmp_path / "summary.json"

    write_outputs(rows, summary, csv_path, json_path)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        saved_rows = list(csv.DictReader(source))
    saved_summary = json.loads(json_path.read_text(encoding="utf-8"))

    assert len(saved_rows) == 1
    assert set(saved_rows[0]) == set(OUTPUT_COLUMNS)
    assert saved_summary["dataset_id"] == DATASET_ID
    assert saved_summary["summary"]["model_trained"] is False
    assert saved_rows[0]["taxonomy_label_preview"] == "legitimate"
    assert "residual_url_domain_candidate" in saved_rows[0]


class FakeSplit(list):
    column_names = [
        "id",
        "text",
        "language",
        "source_dataset",
        "is_scam",
        "head1_social_engineering",
        "head2_scam_intent",
        "split_group",
        "metadata",
    ]


def test_load_huggingface_candidate_uses_all_named_publisher_splits():
    fake = {
        "train": FakeSplit([make_source_row()]),
        "val": FakeSplit([make_source_row(record_id="val")]),
        "test": FakeSplit([make_source_row(record_id="test")]),
    }

    records = load_huggingface_candidate(loader=lambda *args, **kwargs: fake)

    assert {item[0] for item in records} == {"train", "val", "test"}
    assert len(records) == 3


def test_load_huggingface_candidate_rejects_unexpected_split_names():
    fake = {"development": FakeSplit([make_source_row()])}

    with pytest.raises(ValueError, match="Unexpected publisher split"):
        load_huggingface_candidate(loader=lambda *args, **kwargs: fake)


def test_load_huggingface_candidate_rejects_missing_required_columns():
    class IncompleteSplit(list):
        column_names = ["text", "is_scam"]

    fake = {
        "train": IncompleteSplit([{"text": "x", "is_scam": 0}]),
        "val": FakeSplit([make_source_row(record_id="val")]),
        "test": FakeSplit([make_source_row(record_id="test")]),
    }

    with pytest.raises(ValueError, match="missing columns"):
        load_huggingface_candidate(loader=lambda *args, **kwargs: fake)


def test_audit_records_reports_split_group_cardinality_per_source():
    rows = prepare_records(
        [
            ("train", 0, make_source_row(
                record_id="a", text="First unique message", split_group="source_marker"
            )),
            ("val", 0, make_source_row(
                record_id="b", text="Second unique message", split_group="source_marker"
            )),
            ("test", 0, make_source_row(
                record_id="c", text="Third unique message", split_group="campaign_2"
            )),
        ]
    )

    summary = audit_records(rows)
    values = summary["publisher_split_group_cardinality_by_source"]["UCI_SMS_Spam"]

    assert values["rows_with_group_id"] == 3
    assert values["unique_group_ids"] == 2
    assert values["repeated_group_ids"] == 1
    assert values["largest_group_size"] == 2


def test_load_huggingface_candidate_requires_train_validation_and_test():
    fake = {
        "train": FakeSplit([make_source_row()]),
        "test": FakeSplit([make_source_row(record_id="test")]),
    }

    with pytest.raises(ValueError, match="missing required splits"):
        load_huggingface_candidate(loader=lambda *args, **kwargs: fake)


def test_taxonomy_preview_preserves_ambiguous_intents_for_review():
    assert taxonomy_label_preview("Legitimate / Benign") == "legitimate"
    assert taxonomy_label_preview("General Spam / Telemarketing") == "spam"
    assert taxonomy_label_preview("Fake KYC") == "scam"
    assert taxonomy_label_preview("Unmapped / Unknown Intent") == "needs_review"


def test_record_id_prefix_hint_is_explicitly_unverified():
    assert record_id_prefix_hint("real_123") == "real_prefix_unverified"
    assert record_id_prefix_hint("synth_ind_123") == "synthetic_prefix_unverified"
    assert record_id_prefix_hint("custom_123") == "other_prefix_unverified"
    assert record_id_prefix_hint("") == "missing"
