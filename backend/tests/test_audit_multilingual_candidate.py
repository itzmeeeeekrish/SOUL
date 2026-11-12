"""Tests for the privacy-preserving multilingual candidate audit."""

import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_multilingual_candidate import (
    audit_prepared_rows,
    load_huggingface_candidate,
    prepare_candidate_rows,
    script_profile,
    write_audit_outputs,
)


def source_row(text, label, language):
    return {"text": text, "label": label, "language": language}


def records_for_test():
    return [
        ("train", 0, source_row("Your delivery is scheduled tomorrow.", 0, "English")),
        ("train", 1, source_row("आपका खाता बंद हो जाएगा। OTP भेजें।", 1, "Hindi")),
        ("test", 0, source_row("Aapka KYC pending hai. OTP bheje.", 1, "Hinglish")),
        ("test", 1, source_row("Your delivery is scheduled tomorrow.", "ham", "English")),
    ]


def test_script_profile_distinguishes_latin_devanagari_and_mixed():
    assert script_profile("Your bank account") == "latin_only"
    assert script_profile("आपका खाता बंद है") == "devanagari"
    assert script_profile("Your account बंद है") == "mixed_latin_non_latin"


def test_prepare_candidate_rows_preserves_binary_source_task_and_language():
    rows = prepare_candidate_rows(records_for_test())

    assert rows[0]["source_label"] == "ham"
    assert rows[1]["source_label"] == "scam"
    assert rows[1]["label_task"] == "scam_vs_ham"
    assert rows[1]["language"] == "hindi"
    assert rows[1]["source_type"] == "synthetic"
    assert rows[1]["source_split"] == "train"


def test_audit_counts_languages_labels_scripts_and_duplicates():
    rows = prepare_candidate_rows(records_for_test())
    summary = audit_prepared_rows(rows)

    assert summary["total_records"] == 4
    assert summary["label_counts"] == {"ham": 2, "scam": 2}
    assert summary["language_counts"] == {
        "english": 2,
        "hindi": 1,
        "hinglish": 1,
    }
    assert summary["duplicate_text_groups"] == 1
    assert summary["duplicate_groups_crossing_publisher_splits"] == 1
    assert summary["duplicate_groups_with_conflicting_labels"] == 0
    assert summary["script_profile_counts"]["devanagari"] == 1
    assert summary["script_profile_counts"]["latin_only"] == 3
    assert "mixed_latin_non_latin" not in summary["script_profile_counts"]


def test_audit_flags_duplicate_text_with_conflicting_labels():
    input_rows = [
        ("train", 0, source_row("Same message", "ham", "English")),
        ("test", 0, source_row("Same message", "scam", "English")),
    ]
    summary = audit_prepared_rows(prepare_candidate_rows(input_rows))

    assert summary["duplicate_groups_with_conflicting_labels"] == 1


def test_privacy_audit_counts_pattern_candidates_without_exposing_values():
    rows = prepare_candidate_rows(
        [("train", 0, source_row("Call +91 98765 43210", "scam", "English"))]
    )
    summary = audit_prepared_rows(rows)

    assert summary["privacy_candidate_counts"]["has_phone_long_number_candidate"] == 1
    assert summary["privacy_candidate_counts"]["rows_with_any_candidate"] == 1
    assert "+91" not in str(summary)


def test_prepare_candidate_rows_rejects_blank_text():
    with pytest.raises(ValueError, match="Blank text"):
        prepare_candidate_rows(
            [("train", 0, source_row(" ", "ham", "English"))]
        )


def test_prepare_candidate_rows_rejects_unsupported_labels():
    with pytest.raises(ValueError, match="Unsupported source label"):
        prepare_candidate_rows(
            [("train", 0, source_row("Message", "spam", "English"))]
        )


def test_load_huggingface_candidate_preserves_source_split_and_indices():
    calls = []

    class FakeSplit(list):
        pass

    fake_dataset = {
        "train": FakeSplit([source_row("one", 0, "English")]),
        "test": FakeSplit([source_row("two", 1, "Hindi")]),
    }

    def fake_loader(dataset_id, trust_remote_code):
        calls.append((dataset_id, trust_remote_code))
        return fake_dataset

    records = load_huggingface_candidate(fake_loader)

    assert calls == [("anmolshrivastav/scam_ham_india_14_languages", False)]
    assert records == [
        ("train", 0, source_row("one", 0, "English")),
        ("test", 0, source_row("two", 1, "Hindi")),
    ]


def test_load_huggingface_candidate_rejects_missing_expected_split():
    def fake_loader(_dataset_id, trust_remote_code):
        return {"train": []}

    with pytest.raises(ValueError, match="missing expected splits"):
        load_huggingface_candidate(fake_loader)


def test_write_audit_outputs_keeps_text_only_in_private_csv_and_summary_aggregate(tmp_path):
    rows = prepare_candidate_rows(records_for_test())
    summary = audit_prepared_rows(rows)
    csv_path = tmp_path / "private.csv"
    json_path = tmp_path / "summary.json"

    write_audit_outputs(rows, summary, csv_path, json_path)

    csv_text = csv_path.read_text(encoding="utf-8-sig")
    json_text = json_path.read_text(encoding="utf-8")

    assert "Your delivery is scheduled tomorrow." in csv_text
    assert "Your delivery is scheduled tomorrow." not in json_text
    assert '"model_trained": false' in json_text
    assert '"historical_baseline_modified": false' in json_text
    assert '"evaluation_approval": false' in json_text


def test_prepare_candidate_rows_rejects_oversized_text():
    with pytest.raises(ValueError, match="5,000-character"):
        prepare_candidate_rows(
            [("train", 0, source_row("x" * 5001, "ham", "English"))]
        )


def test_prepare_candidate_rows_rejects_missing_language():
    with pytest.raises(ValueError, match="language tag is blank"):
        prepare_candidate_rows(
            [("train", 0, source_row("A normal message.", 0, ""))]
        )
