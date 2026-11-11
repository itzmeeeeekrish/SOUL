import sys
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from validate_prepared_dataset import audit_records


def make_record(record_id="M00001", label="legitimate", text="Appointment tomorrow"):
    return {
        "record_id": record_id,
        "label": label,
        "text": text,
        "source_occurrences": "1",
        "has_url_candidate": "0",
        "has_email_upi_candidate": "0",
        "has_long_number_candidate": "0",
        "has_12_digit_candidate": "0",
        "has_pan_like_candidate": "0",
        "source_url_flag": "0",
        "source_email_flag": "0",
        "source_phone_flag": "0",
    }


def test_valid_records_have_no_schema_value_warnings():
    stats, labels = audit_records([make_record()])

    assert stats["total_records"] == 1
    assert stats["missing_record_ids"] == 0
    assert stats["duplicate_record_id_rows"] == 0
    assert stats["blank_text_rows"] == 0
    assert stats["invalid_label_rows"] == 0
    assert stats["invalid_binary_metadata_values"] == 0
    assert stats["invalid_source_occurrence_values"] == 0
    assert labels["legitimate"] == 1


def test_residual_candidate_patterns_are_counted():
    row = make_record(text="Please visit https://example.com")

    stats, _ = audit_records([row])

    assert stats["residual_candidate_rows"] == 1
    assert stats["residual_url_domain_rows"] == 1


def test_same_masked_text_with_same_label_is_reported_as_collision():
    rows = [
        make_record(record_id="M00001"),
        make_record(record_id="M00002"),
    ]

    stats, _ = audit_records(rows)

    assert stats["masked_text_collision_groups"] == 1
    assert stats["cross_label_masked_text_collision_groups"] == 0


def test_same_masked_text_with_different_labels_is_reported():
    rows = [
        make_record(record_id="M00001", label="scam"),
        make_record(record_id="M00002", label="spam"),
    ]

    stats, _ = audit_records(rows)

    assert stats["masked_text_collision_groups"] == 1
    assert stats["cross_label_masked_text_collision_groups"] == 1


def test_invalid_labels_metadata_and_duplicate_ids_are_counted():
    first = make_record(record_id="M00001", label="unknown")
    first["source_url_flag"] = "yes"
    first["source_occurrences"] = "zero"
    second = make_record(record_id="M00001", label="spam")

    stats, labels = audit_records([first, second])

    assert stats["invalid_label_rows"] == 1
    assert stats["invalid_binary_metadata_values"] == 1
    assert stats["invalid_source_occurrence_values"] == 1
    assert stats["duplicate_record_id_rows"] == 1
    assert labels["spam"] == 1
