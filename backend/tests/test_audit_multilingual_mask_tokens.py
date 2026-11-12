import sys
from pathlib import Path

import pytest


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_multilingual_mask_tokens import (
    build_report,
    calculate_language_label_marker_rates,
    calculate_marker_rates,
)


def row(text, label="scam", language="hindi"):
    return {
        "text": text,
        "label": label,
        "language": language,
    }


def test_marker_rates_count_redaction_tokens_case_insensitively():
    rows = [
        row("Click [URL] now", "scam"),
        row("Visit [domain] for details", "scam"),
        row("Your reminder is ready", "ham"),
    ]

    result = calculate_marker_rates(rows)

    assert result["rows"] == 3
    assert result["overall"]["url"]["messages"] == 1
    assert result["overall"]["domain"]["messages"] == 1
    assert result["by_label"]["scam"]["markers"]["url"]["rate"] == pytest.approx(0.5)
    assert result["by_label"]["ham"]["markers"]["url"]["rate"] == 0.0


def test_marker_rates_handle_empty_markers_and_multiple_labels():
    rows = [
        row("Normal message", "ham"),
        row("Ordinary reminder", "ham"),
        row("Share OTP with [EMAIL_OR_UPI]", "scam"),
    ]

    result = calculate_marker_rates(rows)

    assert result["by_label"]["ham"]["rows"] == 2
    assert result["by_label"]["scam"]["markers"]["email_or_upi"]["messages"] == 1
    assert result["overall"]["long_number"]["rate"] == 0.0


def test_marker_rates_reject_empty_rows():
    with pytest.raises(ValueError, match="empty split"):
        calculate_marker_rates([])


def test_language_label_rates_are_separated_by_language_and_label():
    rows = [
        row("Send [URL]", "scam", "hindi"),
        row("Bank reminder", "ham", "hindi"),
        row("Message [LONG_NUMBER]", "scam", "tamil"),
    ]

    result = calculate_language_label_marker_rates(rows)

    assert result["hindi"]["scam"]["rows"] == 1
    assert result["hindi"]["scam"]["rates"]["url"] == 1.0
    assert result["hindi"]["ham"]["rates"]["url"] == 0.0
    assert result["tamil"]["scam"]["rates"]["long_number"] == 1.0


def test_build_report_marks_test_as_unread_and_model_untrained():
    train = [row("Your reminder", "ham")]
    validation = [row("Click [URL]", "scam")]

    report = build_report(train, validation)

    assert report["test_partition_read"] is False
    assert report["model_trained"] is False
    assert report["train"]["rows"] == 1
    assert report["validation"]["rows"] == 1
