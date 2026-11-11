import sys
from collections import Counter
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from prepare_mendeley_dataset import prepare_rows


def make_row(label, text, url="no", email="no", phone="no"):
    return {
        "LABEL": label,
        "TEXT": text,
        "URL": url,
        "EMAIL": email,
        "PHONE": phone,
    }


def test_conflicting_exact_text_group_is_quarantined():
    rows = [
        make_row("Smishing", "Call 9876543210 to verify your account"),
        make_row("spam", "  CALL 9876543210   TO VERIFY YOUR ACCOUNT "),
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert prepared == []
    assert len(quarantine) == 1
    assert quarantine[0]["reason"] == "conflicting_labels_same_normalised_text"
    assert quarantine[0]["source_occurrences"] == 2
    assert stats["conflict_groups"] == 1
    assert stats["conflict_rows"] == 2


def test_same_label_exact_duplicates_collapse_to_one_redacted_record():
    rows = [
        make_row("ham", "Call 9876543210 for assistance"),
        make_row("HAM", "  call 9876543210   for assistance "),
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert len(prepared) == 1
    assert quarantine == []
    assert prepared[0]["source_label"] == "ham"
    assert prepared[0]["label"] == "legitimate"
    assert prepared[0]["soul_label"] == ""
    assert prepared[0]["review_status"] == "pending"
    assert prepared[0]["annotation_note"] == ""
    assert prepared[0]["source_occurrences"] == 2
    assert "[LONG_NUMBER]" in prepared[0]["text"]
    assert "9876543210" not in prepared[0]["text"]
    assert stats["same_label_duplicate_groups"] == 1
    assert stats["duplicate_rows_collapsed"] == 1


def test_source_labels_map_to_soul_classes():
    rows = [
        make_row("ham", "Your appointment is tomorrow"),
        make_row("smishing", "Visit http://example.com to verify"),
        make_row("Spam", "Special offer at http://example.org"),
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert quarantine == []
    assert Counter(row["source_label"] for row in prepared) == Counter(
        {"ham": 1, "smishing": 1, "spam": 1}
    )
    assert Counter(row["label"] for row in prepared) == Counter(
        {"legitimate": 1, "scam": 1, "spam": 1}
    )
    assert all(row["soul_label"] == "" for row in prepared)
    assert all(row["review_status"] == "pending" for row in prepared)


def test_candidate_identifiers_are_redacted_from_prepared_text():
    rows = [
        make_row(
            "smishing",
            "Call 9876543210 or visit https://example.com now",
            url="yes",
            phone="yes",
        )
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert quarantine == []
    assert len(prepared) == 1
    text = prepared[0]["text"]

    assert "9876543210" not in text
    assert "https://example.com" not in text
    assert "[LONG_NUMBER]" in text
    assert "[URL]" in text
    assert prepared[0]["has_url_candidate"] == 1
    assert prepared[0]["has_long_number_candidate"] == 1


def test_source_flag_mismatch_is_counted():
    rows = [
        make_row(
            "ham",
            "Open https://example.com",
            url="no",
        )
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert len(prepared) == 1
    assert quarantine == []
    assert stats["url_flag_mismatches"] == 1


def test_unknown_label_is_quarantined():
    rows = [
        make_row("unknown", "Call 9876543210 for details")
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert prepared == []
    assert len(quarantine) == 1
    assert quarantine[0]["reason"] == "unknown_label"
    assert stats["unknown_label_rows"] == 1


def test_empty_text_is_quarantined():
    rows = [
        make_row("ham", "   ")
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert prepared == []
    assert len(quarantine) == 1
    assert quarantine[0]["reason"] == "blank_text"
    assert stats["blank_text_rows"] == 1



def test_prepared_record_preserves_original_source_label_separately():
    rows = [
        make_row("Smishing", "Visit http://example.com to verify")
    ]

    prepared, quarantine, stats = prepare_rows(rows)

    assert quarantine == []
    assert len(prepared) == 1
    assert prepared[0]["source_label"] == "smishing"
    assert prepared[0]["label"] == "scam"
    assert prepared[0]["soul_label"] == ""
    assert prepared[0]["review_status"] == "pending"
