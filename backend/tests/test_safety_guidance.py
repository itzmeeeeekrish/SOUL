import sys
from pathlib import Path

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from app.services.safety_guidance import retrieve_official_guidance


def test_kyc_and_url_indicators_retrieve_rbi_kyc_guidance():
    cards = retrieve_official_guidance(
        ["kyc_or_account_update", "url_present"]
    )

    ids = {card["id"] for card in cards}
    assert "rbi_kyc_fraud_2026" in ids
    assert "dot_chakshu" in ids
    assert all(card["source_url"].startswith("https://") for card in cards)


def test_credential_and_payment_indicators_retrieve_rbi_npci_and_reporting_cards():
    cards = retrieve_official_guidance(
        ["credential_request", "payment_request", "upi_context"]
    )

    ids = {card["id"] for card in cards}
    assert "rbi_fame_2024" in ids
    assert "npci_upi_faq" in ids
    assert "dot_chakshu" in ids
    financial = next(
        card for card in cards
        if card["id"] == "i4c_financial_fraud_1930"
    )
    assert "if money has actually been lost" in financial["condition"]


def test_no_indicators_do_not_retrieve_unrelated_guidance():
    assert retrieve_official_guidance([]) == []


def test_guidance_retrieval_is_deterministic_and_limited():
    codes = ["credential_request", "kyc_or_account_update", "url_present"]
    first = retrieve_official_guidance(codes, max_items=2)
    second = retrieve_official_guidance(codes, max_items=2)

    assert first == second
    assert len(first) == 2
    assert all(card["retrieval_method"] == "curated_keyword_rules" for card in first)


def test_invalid_guidance_limit_is_rejected():
    import pytest

    with pytest.raises(ValueError, match="at least 1"):
        retrieve_official_guidance(["url_present"], max_items=0)
