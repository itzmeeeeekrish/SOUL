import sys
from pathlib import Path

import pytest


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_redaction_marker_distribution import build_marker_distribution


def test_marker_distribution_counts_documents_by_split_and_class():
    splits = {
        "train": [
            {"text": "Hello [LONG_NUMBER]", "label": "legitimate"},
            {"text": "Hello again", "label": "legitimate"},
            {"text": "Pay now [LONG_NUMBER] [URL]", "label": "scam"},
            {"text": "Offer [DOMAIN]", "label": "spam"},
        ],
        "validation": [
            {"text": "Receipt [LONG_NUMBER]", "label": "legitimate"},
            {"text": "Normal service update", "label": "legitimate"},
            {"text": "Prize [URL]", "label": "spam"},
        ],
    }

    report = build_marker_distribution(splits)

    train_legitimate = report["splits"]["train"]["by_label"]["legitimate"]
    train_scam = report["splits"]["train"]["by_label"]["scam"]
    assert train_legitimate["support"] == 2
    assert train_legitimate["markers"]["long_number"]["messages_with_marker"] == 1
    assert train_legitimate["markers"]["long_number"]["prevalence"] == 0.5
    assert train_scam["markers"]["url"]["messages_with_marker"] == 1
    assert train_scam["messages_with_any_marker"] == 1


def test_marker_distribution_exports_aggregates_only():
    secret = "PRIVATE-CUSTOMER-TOKEN-87231"
    splits = {
        "train": [
            {"text": f"Message {secret} [LONG_NUMBER]", "label": "legitimate"},
        ],
        "validation": [
            {"text": f"Message {secret}", "label": "scam"},
        ],
    }

    report = build_marker_distribution(splits)

    assert secret not in str(report)
    assert report["privacy"]["message_text_exported"] is False
    assert report["privacy"]["row_ids_exported"] is False
    assert report["scope"]["test_split_read"] is False
    assert report["scope"]["model_retrained"] is False


def test_marker_distribution_rejects_test_or_unknown_split():
    with pytest.raises(ValueError, match="Only train and validation"):
        build_marker_distribution({
            "train": [{"text": "x", "label": "legitimate"}],
            "validation": [{"text": "y", "label": "scam"}],
            "test": [{"text": "z", "label": "spam"}],
        })


def test_marker_distribution_rejects_empty_split():
    with pytest.raises(ValueError, match="must not be empty"):
        build_marker_distribution({
            "train": [],
            "validation": [{"text": "y", "label": "scam"}],
        })


def test_marker_distribution_rejects_invalid_label():
    with pytest.raises(ValueError, match="unsupported label"):
        build_marker_distribution({
            "train": [{"text": "x", "label": "other"}],
            "validation": [{"text": "y", "label": "scam"}],
        })
