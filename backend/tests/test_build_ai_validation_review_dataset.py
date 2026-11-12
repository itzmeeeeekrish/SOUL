"""Tests for provenance-preserving AI silver-label export."""

import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from build_ai_validation_review_dataset import build_ai_review_rows


def blind_row(review_id="R1", text="A sample message"):
    return {
        "review_id": review_id,
        "text": text,
        "soul_label": "",
        "review_status": "pending",
        "annotation_note": "",
    }


def suggestion_row(review_id="R1", label="spam", status="provisional_suggestion"):
    return {
        "review_id": review_id,
        "ai_provisional_label": label,
        "ai_review_status": status,
        "ai_annotation_note": "Text-only AI rationale.",
    }


def test_build_keeps_ai_labels_separate_from_official_review_fields():
    rows = build_ai_review_rows(
        [blind_row("R1"), blind_row("R2")],
        [
            suggestion_row("R1", "spam"),
            suggestion_row("R2", "needs_review", "needs_more_context"),
        ],
        created_date="2026-11-12",
    )

    assert len(rows) == 2
    assert rows[0]["ai_suggested_label"] == "spam"
    assert rows[0]["ai_annotation_status"] == "provisional"
    assert rows[1]["ai_suggested_label"] == "needs_review"
    assert rows[1]["ai_annotation_status"] == "needs_review"
    for row in rows:
        assert row["soul_label"] == ""
        assert row["review_status"] == "pending"
        assert row["annotation_note"] == ""
        assert row["ai_annotator"] == "ChatGPT"
        assert row["ai_model"] == "GPT-6"
        assert row["ai_created_date"] == "2026-11-12"



def test_build_maps_blank_ai_label_with_needs_context_status_to_abstention():
    suggestion = suggestion_row(label="", status="needs_more_context")

    rows = build_ai_review_rows([blind_row()], [suggestion])

    assert rows[0]["ai_suggested_label"] == "needs_review"
    assert rows[0]["ai_annotation_status"] == "needs_review"

def test_build_rejects_mismatched_review_ids():
    with pytest.raises(ValueError, match="Review IDs do not match"):
        build_ai_review_rows([blind_row("R1")], [suggestion_row("R2")])


def test_build_rejects_duplicate_review_ids():
    with pytest.raises(ValueError, match="duplicate review_id"):
        build_ai_review_rows(
            [blind_row("R1"), blind_row("R1", "Another message")],
            [suggestion_row("R1")],
        )


def test_build_rejects_unsupported_ai_label():
    with pytest.raises(ValueError, match="unsupported label"):
        build_ai_review_rows(
            [blind_row()],
            [suggestion_row(label="high_risk")],
        )


def test_build_rejects_ai_label_status_mismatch():
    with pytest.raises(ValueError, match="needs_more_context"):
        build_ai_review_rows(
            [blind_row()],
            [suggestion_row(label="needs_review", status="provisional_suggestion")],
        )


def test_build_refuses_to_overwrite_existing_official_review():
    completed = blind_row()
    completed["soul_label"] = "scam"
    completed["review_status"] = "reviewed"

    with pytest.raises(ValueError, match="already contains a SOUL label"):
        build_ai_review_rows([completed], [suggestion_row()])


def test_build_neutralises_formula_like_text():
    rows = build_ai_review_rows(
        [blind_row(text="=HYPERLINK('bad')")],
        [suggestion_row()],
    )

    assert rows[0]["text"].startswith("'=HYPERLINK")
