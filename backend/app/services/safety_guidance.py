"""Curated official safety guidance with transparent keyword-based retrieval.

This is a small rule-based retrieval prototype, not a full vector-search or
LLM-based RAG pipeline. Content is paraphrased from official public sources.
"""


KNOWLEDGE_BASE_VERSION = "soul-official-guidance-v0.1"
RETRIEVED_DATE = "2026-11-14"

GUIDANCE_CARDS = [
    {
        "id": "rbi_kyc_fraud_2026",
        "issuer": "Reserve Bank of India",
        "title": "RBI public guidance: beware of KYC fraud",
        "advice": (
            "Do not enter KYC details through an unknown link. Verify the sender "
            "before clicking. RBI guidance says not to share OTPs, PINs, passwords "
            "or confidential information, and to ignore messages creating false urgency."
        ),
        "source_url": (
            "https://www.rbi.org.in/FinancialEducation/FLW2026/English/"
            "69656_RBI%20FLW%20KYC%20Fraud%20POSM_Leaflet%20A5.pdf"
        ),
        "source_date": "RBI Financial Literacy Week 2026 public-awareness leaflet",
        "trigger_codes": {
            "kyc_or_account_update",
            "url_present",
            "urgency_or_threat",
        },
        "condition": "Relevant when KYC, link or urgency wording is present.",
    },
    {
        "id": "rbi_fame_2024",
        "issuer": "Reserve Bank of India",
        "title": "RBI Financial Awareness Messages: electronic banking",
        "advice": (
            "Never share mobile-banking PIN, internet-banking ID/password or OTP "
            "with anyone, including someone claiming to be bank staff. Use trusted "
            "banking websites and inform your bank immediately about an unusual "
            "or unauthorised transaction."
        ),
        "source_url": "https://www.rbi.org.in/commonperson/images/FAME202426022024.pdf",
        "source_date": "Fourth edition, February 2024",
        "trigger_codes": {
            "credential_request",
            "payment_request",
        },
        "condition": "Relevant when credential or payment wording is present.",
    },
    {
        "id": "npci_upi_faq",
        "issuer": "National Payments Corporation of India",
        "title": "NPCI UPI FAQ: protect your UPI PIN",
        "advice": (
            "Do not share your UPI PIN. It is used to authorise UPI transactions; "
            "the NPCI FAQ says bank customer support will never ask for it."
        ),
        "source_url": "https://www.npci.org.in/what-we-do/upi/faqs",
        "source_date": "Official NPCI UPI FAQ; accessed 14 November 2026",
        "trigger_codes": {"upi_context"},
        "condition": "Relevant when UPI, PIN or payment wording is present.",
    },
    {
        "id": "dot_chakshu",
        "issuer": "Department of Telecommunications, Government of India",
        "title": "Chakshu: report suspected fraud communications",
        "advice": (
            "For a suspected fraudulent call, SMS or WhatsApp communication, "
            "citizens can use the Chakshu facility on the Sanchar Saathi platform. "
            "Keep relevant details such as the communication channel, category, "
            "date/time and screenshot if available."
        ),
        "source_url": (
            "https://sancharsaathi.gov.in/SancharSaathiDocuments/ImportantDocuments/"
            "DoT%20Press%20Release-%20Hon%27ble%20Union%20Minister%20of%20Communications"
            "%20Shri%20Ashwini%20Vaishnaw%20launches%20Digital%20Intelligence%20Platform"
            "%20%26%20Chakshu%20Module%20on%20Sanchar%20Saathi%20-%2004.03.2024.pdf"
        ),
        "source_date": "DoT / PIB public information, 4 March 2024",
        "trigger_codes": {
            "credential_request",
            "urgency_or_threat",
            "kyc_or_account_update",
            "url_present",
            "remote_access_request",
            "payment_request",
        },
        "condition": "For suspected fraud communications; reporting is user-initiated.",
    },
    {
        "id": "i4c_financial_fraud_1930",
        "issuer": "Indian Cyber Crime Coordination Centre / Ministry of Home Affairs",
        "title": "If money has already been lost: report financial cyber fraud",
        "advice": (
            "If a financial cyber fraud has already happened or money has been "
            "debited, contact your bank immediately and report promptly using "
            "the 1930 cybercrime helpline or the National Cyber Crime Reporting Portal."
        ),
        "source_url": "https://cybercrime.gov.in/",
        "source_date": "Official National Cyber Crime Reporting Portal; accessed 14 November 2026",
        "trigger_codes": {
            "payment_request",
            "credential_request",
            "remote_access_request",
        },
        "condition": (
            "Conditional guidance only: use this route if money has actually been "
            "lost or an unauthorised transaction has occurred; a suspicious message "
            "alone does not mean a financial loss has happened."
        ),
    },
]


def retrieve_official_guidance(indicator_codes, max_items=4):
    """Return relevant source cards in a stable, deterministic order."""
    if max_items < 1:
        raise ValueError("max_items must be at least 1.")

    codes = set(indicator_codes or [])
    matches = []
    for card in GUIDANCE_CARDS:
        overlap = sorted(codes.intersection(card["trigger_codes"]))
        if not overlap:
            continue
        matches.append({
            "id": card["id"],
            "issuer": card["issuer"],
            "title": card["title"],
            "advice": card["advice"],
            "source_url": card["source_url"],
            "source_date": card["source_date"],
            "retrieved_date": RETRIEVED_DATE,
            "relevance_reason": overlap,
            "condition": card["condition"],
            "retrieval_method": "curated_keyword_rules",
            "knowledge_base_version": KNOWLEDGE_BASE_VERSION,
        })

    return matches[:max_items]
