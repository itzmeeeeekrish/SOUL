"""Tests for the privacy-preserving language coverage audit."""

import sys
from pathlib import Path

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_language_coverage import audit_language_rows


def test_audit_returns_aggregate_counts_without_message_text():
    rows = [
        {"text": "Your delivery is scheduled."},
        {"text": "आपका खाता बंद हो जाएगा"},
        {"text": "Aapka bank khata band hai"},
        {"text": "Your account बंद हो जाएगा"},
    ]

    total, counts = audit_language_rows(rows)

    assert total == 4
    assert counts["latin_without_hinglish_markers"] == 1
    assert counts["romanized_hindi_signal"] == 1
    assert counts["mixed_script"] == 1
    assert counts["non_latin_script"] == 1
