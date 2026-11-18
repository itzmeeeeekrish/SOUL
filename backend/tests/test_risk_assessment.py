"""Regression tests for the independent risk evidence layer."""

import pytest

from app.services.risk_assessment import assess_message_risk


@pytest.mark.parametrize(
    "text, expected_code",
    [
        (
            "A bank support agent says enter your UPI PIN to release a refund. "
            "Approve the collect request immediately.",
            "credential_disclosure_request",
        ),
        (
            "Customs payment is pending. Pay the parcel fee now or your parcel "
            "will be returned at https://parcel.example/clear.",
            "payment_under_threat_or_authority_pressure",
        ),
        (
            "Your remote job is confirmed. Pay a registration deposit today "
            "to activate the offer and secure your joining letter.",
            "upfront_fee_for_job_or_benefit",
        ),
        (
            "I am your nephew using a new number. Transfer money to this new "
            "UPI ID urgently and do not call the family.",
            "family_impersonation_transfer_pressure",
        ),
        (
            "Electricity disconnection warning: pay outstanding dues immediately "
            "at https://power.example/restore.",
            "payment_under_threat_or_authority_pressure",
        ),
        (
            "A police case is pending against your identity. Pay the penalty "
            "immediately to avoid arrest.",
            "payment_under_threat_or_authority_pressure",
        ),
        (
            "Your insurance refund is ready. Send the refund fee first to "
            "activate the transfer.",
            "upfront_fee_for_job_or_benefit",
        ),
        (
            "Install AnyDesk and share your screen so I can fix the bank refund. "
            "Keep your banking app open during the session.",
            "remote_access_with_financial_context",
        ),
        (
            "A bank representative asks you to install AnyDesk for screen sharing "
            "and keep your phone unlocked during the refund process.",
            "remote_access_with_financial_context",
        ),
        (
            "The delivery agent needs the parcel OTP. Tell us the code over this "
            "call to complete delivery.",
            "credential_disclosure_request",
        ),
    ],
)
def test_flags_high_concern_action_and_context_combinations(text, expected_code):
    result = assess_message_risk(text)

    assert result["concern_level"] == "high"
    assert expected_code in {item["code"] for item in result["evidence"]}
    assert result["review_required"] is True
    assert "proof" in result["notice"]


@pytest.mark.parametrize(
    "text, expected_level",
    [
        ("Your annual KYC review is due. Visit your bank branch for instructions.", "limited"),
        ("Your electricity bill payment has been received.", "no_strong_signal"),
        ("Your salary for November has been credited. Check your payslip.", "no_strong_signal"),
        ("Weekend offer: selected kitchen products are available at reduced prices.", "no_strong_signal"),
        ("Review this link: https://shop.example/sale", "limited"),
        ("Urgent: last day to renew your newspaper subscription at a discounted rate.", "limited"),
        ("Never share your OTP or PIN with anyone. Contact the bank independently.", "needs_review"),
    ],
)
def test_benign_or_low_specificity_lookalikes_do_not_become_high_concern(
    text, expected_level
):
    result = assess_message_risk(text)

    assert result["concern_level"] == expected_level
    assert result["concern_level"] != "high"


def test_urgent_kyc_link_is_elevated_not_automatically_high():
    result = assess_message_risk(
        "URGENT: Update KYC now at https://example.invalid"
    )

    assert result["concern_level"] == "elevated"
    assert "kyc_link_with_urgency" in {
        item["code"] for item in result["evidence"]
    }


def test_payment_wording_alone_is_not_high_concern():
    result = assess_message_risk("Pay Rs 199 for our entertainment subscription.")

    assert result["concern_level"] == "limited"
    assert result["evidence"] == []


def test_unsupported_language_is_always_sent_for_review():
    result = assess_message_risk(
        "कृपया अपना OTP बताएं।",
        language_supported=False,
    )

    assert result["concern_level"] == "needs_review"
    assert result["status"] == "limited_language_support"
    assert "absence of matches" in result["summary"]


def test_evidence_output_does_not_echo_message_or_url():
    secret_url = "https://private.example/account?token=not-for-output"
    result = assess_message_risk(
        f"URGENT: Update KYC at {secret_url} and share your OTP."
    )

    serialized = str(result)
    assert secret_url not in serialized
    assert "not-for-output" not in serialized
