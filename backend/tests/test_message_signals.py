import sys
from pathlib import Path

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from app.services.message_signals import extract_message_indicators


def codes(text):
    return extract_message_indicators(text)["indicator_codes"]


def test_detects_credential_request_without_exposing_message_text():
    result = extract_message_indicators(
        "Your account is blocked. Share your OTP and UPI PIN now."
    )

    assert "credential_request" in result["indicator_codes"]
    assert "upi_context" in result["indicator_codes"]
    assert "urgency_or_threat" in result["indicator_codes"]
    assert all("OTP" not in item["explanation"] for item in result["indicators"])
    assert "not proof of fraud" in result["notice"]


def test_does_not_flag_safety_warning_as_credential_request():
    assert "credential_request" not in codes(
        "Never share your OTP or PIN with anyone."
    )


def test_detects_kyc_link_and_urgency_indicators():
    result = extract_message_indicators(
        "URGENT: Update your KYC immediately at https://example.invalid"
    )
    found = set(result["indicator_codes"])

    assert {"kyc_or_account_update", "url_present", "urgency_or_threat"} <= found


def test_url_indicator_does_not_claim_destination_was_checked():
    result = extract_message_indicators(
        "Review this link https://example.invalid"
    )
    url_signal = next(
        item for item in result["indicators"]
        if item["code"] == "url_present"
    )

    assert "has not opened it" in url_signal["explanation"]
    assert "example.invalid" not in str(result)


def test_detects_remote_access_and_payment_wording():
    found = set(codes(
        "Install AnyDesk for remote access and transfer the processing fee."
    ))

    assert "remote_access_request" in found
    assert "payment_request" in found


def test_payment_confirmation_receipt_does_not_trigger_payment_request():
    result = extract_message_indicators(
        "Your electricity bill payment has been received. "
        "The receipt is available in your customer account."
    )

    assert "payment_request" not in result["indicator_codes"]


def test_explicit_payment_demand_still_triggers_payment_request():
    result = extract_message_indicators(
        "Your parcel fee is pending. Pay the amount now to release delivery."
    )

    assert "payment_request" in result["indicator_codes"]


def test_empty_text_returns_no_indicators():
    result = extract_message_indicators("")

    assert result["indicators"] == []
    assert result["indicator_codes"] == []



def test_detects_standalone_protective_credential_warning_as_context():
    result = extract_message_indicators(
        "Never share your OTP or PIN with anyone. Use your bank's official app."
    )

    assert result["indicator_codes"] == []
    assert result["context_flags"][0]["code"] == "protective_credential_warning"


def test_does_not_treat_mixed_warning_and_urgent_link_as_warning_only():
    result = extract_message_indicators(
        "Never share your OTP. URGENT: Update KYC at https://example.invalid"
    )

    assert result["context_flags"] == []
    assert {"urgency_or_threat", "kyc_or_account_update", "url_present"} <= set(
        result["indicator_codes"]
    )
