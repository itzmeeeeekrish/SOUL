"""Extract transparent, low-risk text indicators for message review.

These rules are advisory keyword patterns only. They do not prove fraud,
verify a URL, establish sender identity, or change the ML model prediction.
"""

import re


PATTERNS = {
    "credential_request": re.compile(
        r"\b(?:otp|one[ -]?time password|upi[ -]?pin|pin|cvv|password|passcode|"
        r"login credentials|banking credentials)\b",
        re.IGNORECASE,
    ),
    "credential_request_verbs": re.compile(
        r"\b(?:share|send|provide|enter|submit|reply with|tell us|confirm|"
        r"verify|update)\b",
        re.IGNORECASE,
    ),
    "credential_negation": re.compile(
        r"\b(?:do not|don't|dont|never|avoid|never ever)\s+"
        r"(?:share|send|provide|enter|submit|reply with|tell)\b",
        re.IGNORECASE,
    ),
    "urgency_or_threat": re.compile(
        r"\b(?:urgent|immediately|right away|final warning|"
        r"account (?:will be|is) (?:blocked|suspended|closed|deactivated)|"
        r"account (?:block|suspend|close|deactivate)|"
        r"within\s+\d+\s+(?:hours?|minutes?|days?)|"
        r"expires? (?:today|soon|in) )\b",
        re.IGNORECASE,
    ),
    "kyc_or_account_update": re.compile(
        r"\b(?:kyc|re[ -]?kyc|know your customer|account verification|"
        r"verify your account|update your account|update account details)\b",
        re.IGNORECASE,
    ),
    "url_present": re.compile(
        r"(?:https?://|www\.)[^\s<>]+",
        re.IGNORECASE,
    ),
    "upi_context": re.compile(r"\bupi\b", re.IGNORECASE),
    "remote_access_request": re.compile(
        r"\b(?:anydesk|teamviewer|remote access|screen share|"
        r"screen sharing|install (?:this|the) app|download (?:this|the) app|"
        r"install an apk)\b",
        re.IGNORECASE,
    ),
    "payment_request": re.compile(
        r"\b(?:pay|payment|transfer|send money|processing fee|"
        r"refund fee|collect request|deposit|upi transfer)\b",
        re.IGNORECASE,
    ),
}


INDICATOR_DETAILS = {
    "credential_request": {
        "title": "Credential-related request language",
        "explanation": (
            "The message contains credential terms and request-style wording. "
            "This is a text signal only; review the full context."
        ),
        "severity_hint": "review",
    },
    "urgency_or_threat": {
        "title": "Urgency or account-threat language",
        "explanation": (
            "The message uses urgency or account-action wording that can "
            "pressure a recipient. Urgency alone does not prove fraud."
        ),
        "severity_hint": "review",
    },
    "kyc_or_account_update": {
        "title": "KYC or account-update language",
        "explanation": (
            "The message refers to KYC or account verification. Check through "
            "the organisation's official app or known contact details."
        ),
        "severity_hint": "review",
    },
    "url_present": {
        "title": "URL-like text present",
        "explanation": (
            "A URL-like string appears in the message. SOUL has not opened it, "
            "resolved redirects, checked reputation, or verified ownership."
        ),
        "severity_hint": "review",
    },
    "upi_context": {
        "title": "UPI-related wording",
        "explanation": (
            "The message refers to UPI. SOUL has not inspected a UPI transaction "
            "or verified the intended payee."
        ),
        "severity_hint": "review",
    },
    "remote_access_request": {
        "title": "Remote-access or app-install wording",
        "explanation": (
            "The message mentions remote access, screen sharing, or installing "
            "an app. Do not install remote-access software at an unsolicited caller's request."
        ),
        "severity_hint": "review",
    },
    "payment_request": {
        "title": "Payment-related wording",
        "explanation": (
            "The message contains payment or transfer wording. A payment mention "
            "alone is not proof of fraud; verify the request independently."
        ),
        "severity_hint": "review",
    },
}


def extract_message_indicators(text):
    """Return category-level indicators without echoing matched text or PII."""
    cleaned = str(text or "")
    found = []

    credential_present = bool(PATTERNS["credential_request"].search(cleaned))
    asks_for_credential = bool(
        PATTERNS["credential_request_verbs"].search(cleaned)
    )
    explicitly_discourages_sharing = bool(
        PATTERNS["credential_negation"].search(cleaned)
    )
    if credential_present and asks_for_credential and not explicitly_discourages_sharing:
        found.append("credential_request")

    for code in (
        "urgency_or_threat",
        "kyc_or_account_update",
        "url_present",
        "upi_context",
        "remote_access_request",
        "payment_request",
    ):
        if PATTERNS[code].search(cleaned):
            found.append(code)

    indicators = [
        {
            "code": code,
            "title": INDICATOR_DETAILS[code]["title"],
            "explanation": INDICATOR_DETAILS[code]["explanation"],
            "severity_hint": INDICATOR_DETAILS[code]["severity_hint"],
        }
        for code in found
    ]

    return {
        "indicators": indicators,
        "indicator_codes": found,
        "notice": (
            "Indicators are simple text-pattern matches, not proof of fraud. "
            "They are not model features and do not change the model's class."
        ),
    }
