import sys
from collections import Counter
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from build_privacy_review_queue import collect_review_groups


def test_same_masked_template_is_grouped_together():
    rows = [
        {
            "LABEL": "smishing",
            "TEXT": "Call 9876543210 to verify your account",
        },
        {
            "LABEL": "smishing",
            "TEXT": "Call 9123456789 to verify your account",
        },
    ]

    groups = collect_review_groups(rows)

    assert len(groups) == 1
    assert groups[0]["source_occurrences"] == 2
    assert groups[0]["source_label_counts"] == Counter({"smishing": 2})
    assert "phone_long_number" in groups[0]["candidate_patterns"]


def test_same_masked_template_with_different_labels_is_preserved_as_conflict():
    rows = [
        {
            "LABEL": "smishing",
            "TEXT": "Call 9876543210 to verify your account",
        },
        {
            "LABEL": "spam",
            "TEXT": "Call 9123456789 to verify your account",
        },
    ]

    groups = collect_review_groups(rows)

    assert len(groups) == 1
    assert groups[0]["source_occurrences"] == 2
    assert groups[0]["source_label_counts"] == Counter(
        {"smishing": 1, "spam": 1}
    )


def test_different_masked_templates_stay_in_separate_groups():
    rows = [
        {
            "LABEL": "smishing",
            "TEXT": "Call 9876543210 to verify your account",
        },
        {
            "LABEL": "spam",
            "TEXT": "Visit http://example.com for an offer",
        },
    ]

    groups = collect_review_groups(rows)

    assert len(groups) == 2


def test_messages_without_candidate_patterns_are_not_added():
    rows = [
        {
            "LABEL": "ham",
            "TEXT": "Your appointment is scheduled for tomorrow",
        }
    ]

    assert collect_review_groups(rows) == []
