import sys
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from validate_prepared_dataset import audit_records


SOURCE_FOR_LABEL = {
    "legitimate": "ham",
    "scam": "smishing",
    "spam": "spam",
}


def make_record(
    record_id="M00001",
    label="legitimate",
    text="Appointment tomorrow",
    source_label=None,
    soul_label="",
    review_status="pending",
    annotation_note="",
):
    if source_label is None:
        source_label = SOURCE_FOR_LABEL.get(label, "ham")

    return {
        "record_id": record_id,
        "source_label": source_label,
        "label": label,
        "soul_label": soul_label,
        "review_status": review_status,
        "annotation_note": annotation_note,
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


def test_valid_pending_record_has_separate_source_and_soul_labels():
    stats, labels, source_labels, review_statuses = audit_records([make_record()])

    assert stats["total_records"] == 1
    assert stats["missing_record_ids"] == 0
    assert stats["duplicate_record_id_rows"] == 0
    assert stats["blank_text_rows"] == 0
    assert stats["invalid_source_label_rows"] == 0
    assert stats["invalid_label_rows"] == 0
    assert stats["provisional_label_mismatch_rows"] == 0
    assert stats["invalid_soul_label_rows"] == 0
    assert stats["invalid_review_status_rows"] == 0
    assert stats["review_state_mismatch_rows"] == 0
    assert stats["invalid_binary_metadata_values"] == 0
    assert stats["invalid_source_occurrence_values"] == 0
    assert stats["pending_review_rows"] == 1
    assert labels["legitimate"] == 1
    assert source_labels["ham"] == 1
    assert review_statuses["pending"] == 1


def test_reviewed_record_requires_soul_label_and_annotation_note():
    row = make_record(
        source_label="smishing",
        label="scam",
        soul_label="spam",
        review_status="reviewed",
        annotation_note="Reviewed as unsolicited promotion without a deceptive request.",
    )

    stats, labels, source_labels, review_statuses = audit_records([row])

    assert stats["review_state_mismatch_rows"] == 0
    assert stats["reviewed_rows"] == 1
    assert labels["scam"] == 1
    assert source_labels["smishing"] == 1
    assert review_statuses["reviewed"] == 1


def test_needs_review_state_requires_needs_review_label_and_note():
    row = make_record(
        soul_label="needs_review",
        review_status="needs_review",
        annotation_note="The message context is insufficient.",
    )

    stats, _, _, review_statuses = audit_records([row])

    assert stats["review_state_mismatch_rows"] == 0
    assert stats["needs_review_rows"] == 1
    assert review_statuses["needs_review"] == 1


def test_inconsistent_review_state_is_counted():
    row = make_record(
        soul_label="",
        review_status="reviewed",
        annotation_note="No label chosen.",
    )

    stats, _, _, _ = audit_records([row])

    assert stats["review_state_mismatch_rows"] == 1


def test_source_label_and_provisional_label_mapping_must_match():
    row = make_record(
        source_label="ham",
        label="scam",
    )

    stats, _, _, _ = audit_records([row])

    assert stats["provisional_label_mismatch_rows"] == 1


def test_residual_candidate_patterns_are_counted():
    row = make_record(text="Please visit https://example.com")

    stats, _, _, _ = audit_records([row])

    assert stats["residual_candidate_rows"] == 1
    assert stats["residual_url_domain_rows"] == 1


def test_same_masked_text_with_same_label_is_reported_as_collision():
    rows = [
        make_record(record_id="M00001"),
        make_record(record_id="M00002"),
    ]

    stats, _, _, _ = audit_records(rows)

    assert stats["masked_text_collision_groups"] == 1
    assert stats["cross_label_masked_text_collision_groups"] == 0


def test_same_masked_text_with_different_labels_is_reported():
    rows = [
        make_record(record_id="M00001", label="scam"),
        make_record(record_id="M00002", label="spam"),
    ]

    stats, _, _, _ = audit_records(rows)

    assert stats["masked_text_collision_groups"] == 1
    assert stats["cross_label_masked_text_collision_groups"] == 1


def test_invalid_labels_metadata_and_duplicate_ids_are_counted():
    first = make_record(record_id="M00001", label="unknown")
    first["source_url_flag"] = "yes"
    first["source_occurrences"] = "zero"
    second = make_record(record_id="M00001", label="spam")

    stats, labels, source_labels, review_statuses = audit_records([first, second])

    assert stats["invalid_label_rows"] == 1
    assert stats["provisional_label_mismatch_rows"] == 1
    assert stats["invalid_binary_metadata_values"] == 1
    assert stats["invalid_source_occurrence_values"] == 1
    assert stats["duplicate_record_id_rows"] == 1
    assert labels["spam"] == 1
    assert source_labels["spam"] == 1
    assert review_statuses["pending"] == 2


def test_invalid_source_and_soul_labels_are_counted():
    row = make_record(
        source_label="unknown",
        soul_label="fraud",
    )

    stats, _, _, _ = audit_records([row])

    assert stats["invalid_source_label_rows"] == 1
    assert stats["invalid_soul_label_rows"] == 1
    assert stats["provisional_label_mismatch_rows"] == 1
