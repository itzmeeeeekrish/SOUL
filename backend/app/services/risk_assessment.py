"""Independent, conservative rule-based risk evidence assessment.

This layer reports combinations of text evidence separately from the ML label.
It does not decide that a message is fraudulent, verify the sender, inspect URLs,
or replace the classifier. Patterns are currently English-oriented.
"""

import re

from app.services.message_signals import extract_message_indicators


PATTERNS = {
    "financial_context": re.compile(
        r"\\b(?:bank|banking|account|upi|refund|card|transaction|wallet|"
        r"kyc|loan|insurance|payment)\\b",
        re.IGNORECASE,
    ),
    "authority_context": re.compile(
        r"\\b(?:bank support|bank representative|bank agent|customer support|"
        r"police|officer|law enforcement|customs|courier|delivery agent|"
        r"electricity board|government|income tax|tax department|"
        r"insurance company)\\b",
        re.IGNORECASE,
    ),
    "delivery_context": re.compile(
        r"\\b(?:parcel|courier|delivery|customs)\\b",
        re.IGNORECASE,
    ),
    "essential_service_context": re.compile(
        r"\\b(?:electricity|power supply|water supply|broadband|mobile service)\\b",
        re.IGNORECASE,
    ),
    "pressure_or_consequence": re.compile(
        r"\\b(?:avoid arrest|arrest|legal action|police case|penalty|"
        r"parcel (?:will be )?returned|returned to sender|"
        r"will be disconnected|disconnection|disconnect(?:ed|ion)?|"
        r"account.{0,35}(?:blocked|suspended|closed|deactivated)|"
        r"service.{0,35}(?:stopped|disconnected|terminated))\\b",
        re.IGNORECASE,
    ),
    "family_identity": re.compile(
        r"\\b(?:nephew|niece|son|daughter|brother|sister|cousin|"
        r"mother|father|uncle|aunt|relative)\\b",
        re.IGNORECASE,
    ),
    "new_contact_claim": re.compile(
        r"\\b(?:new number|new phone|different number|changed number)\\b",
        re.IGNORECASE,
    ),
    "discourage_independent_contact": re.compile(
        r"\\b(?:do not|don't|dont|avoid)\\s+(?:call|contact|verify)\\b"
        r".{0,45}\\b(?:family|bank|office|official|anyone)\\b|"
        r"\\bdo not call (?:your )?(?:family|bank|them)\\b",
        re.IGNORECASE,
    ),
    "upfront_fee_context": re.compile(
        r"\\b(?:registration|processing|security|refundable|advance|"
        r"verification|refund|joining|activation)\\s+(?:fee|deposit|charge)\\b|"
        r"\\b(?:fee|deposit|charge)\\s+(?:first|upfront)\\b",
        re.IGNORECASE,
    ),
    "job_or_benefit_context": re.compile(
        r"\\b(?:job|employment|recruitment|joining|salary|job offer|"
        r"loan|prize|reward|refund|insurance claim|grant|subsidy)\\b",
        re.IGNORECASE,
    ),
}


EVIDENCE_DETAILS = {
    "credential_disclosure_request": {
        "level": "high",
        "title": "Request to disclose a sensitive credential",
        "explanation": (
            "The text appears to ask the recipient to share, enter or disclose "
            "an OTP, PIN, password or similar credential. Do not disclose it "
            "in response to an unexpected message or call."
        ),
    },
    "remote_access_with_financial_context": {
        "level": "high",
        "title": "Remote access requested in a financial context",
        "explanation": (
            "Remote-access or screen-sharing wording appears alongside banking, "
            "account, payment or refund context. Do not install or operate such "
            "software at an unsolicited person's request."
        ),
    },
    "payment_under_threat_or_authority_pressure": {
        "level": "high",
        "title": "Payment linked to pressure or an authority claim",
        "explanation": (
            "Payment wording appears with a claimed authority, service, delivery "
            "or legal consequence and pressure to act. Verify independently before "
            "paying or using the supplied contact details."
        ),
    },
    "family_impersonation_transfer_pressure": {
        "level": "high",
        "title": "Family-identity claim combined with transfer pressure",
        "explanation": (
            "A family relationship and a new-contact claim appear alongside a "
            "money request and wording discouraging independent contact. Contact "
            "the family member using a number you already trust."
        ),
    },
    "upfront_fee_for_job_or_benefit": {
        "level": "high",
        "title": "Upfront fee linked to a job or promised benefit",
        "explanation": (
            "An upfront fee or deposit appears linked to a job, joining process, "
            "refund, prize, loan or other promised benefit. Verify the organisation "
            "independently before sending money."
        ),
    },
    "kyc_link_with_urgency": {
        "level": "elevated",
        "title": "Urgent KYC or account update linked to a URL",
        "explanation": (
            "KYC or account-update wording appears with urgency and a URL. SOUL "
            "has not checked the destination; use the organisation's official app "
            "or a known contact channel instead."
        ),
    },
}


def _has(pattern_name, text):
    return bool(PATTERNS[pattern_name].search(text))


def _evidence(code):
    details = EVIDENCE_DETAILS[code]
    return {
        "code": code,
        "level": details["level"],
        "title": details["title"],
        "explanation": details["explanation"],
    }


def assess_message_risk(text, signal_assessment=None, language_supported=True):
    """Return independent risk evidence without changing an ML prediction.

    The returned concern level is a rule-based advisory, not a fraud verdict
    or calibrated probability. Low-specificity indicators never create a high
    concern by themselves.
    """
    cleaned = str(text or "").strip()
    signals = signal_assessment or extract_message_indicators(cleaned)
    indicator_codes = set(signals.get("indicator_codes", []))
    context_codes = {
        item.get("code") for item in signals.get("context_flags", [])
    }

    evidence_codes = set()
    if "credential_request" in indicator_codes:
        evidence_codes.add("credential_disclosure_request")

    financial_context = _has("financial_context", cleaned)
    authority_context = _has("authority_context", cleaned)
    delivery_context = _has("delivery_context", cleaned)
    service_context = _has("essential_service_context", cleaned)
    pressure = (
        "urgency_or_threat" in indicator_codes
        or _has("pressure_or_consequence", cleaned)
    )
    payment_request = "payment_request" in indicator_codes
    has_url = "url_present" in indicator_codes

    if (
        "remote_access_request" in indicator_codes
        and (financial_context or payment_request)
    ):
        evidence_codes.add("remote_access_with_financial_context")

    if payment_request and pressure and (
        authority_context
        or delivery_context
        or service_context
        or (authority_context and has_url)
    ):
        evidence_codes.add("payment_under_threat_or_authority_pressure")

    family_impersonation = (
        _has("family_identity", cleaned)
        and _has("new_contact_claim", cleaned)
        and _has("discourage_independent_contact", cleaned)
    )
    if family_impersonation and payment_request:
        evidence_codes.add("family_impersonation_transfer_pressure")

    upfront_fee = _has("upfront_fee_context", cleaned)
    job_or_benefit = _has("job_or_benefit_context", cleaned)
    if upfront_fee and job_or_benefit and payment_request:
        evidence_codes.add("upfront_fee_for_job_or_benefit")

    if (
        "kyc_or_account_update" in indicator_codes
        and has_url
        and pressure
    ):
        evidence_codes.add("kyc_link_with_urgency")

    evidence = [
        _evidence(code)
        for code in EVIDENCE_DETAILS
        if code in evidence_codes
    ]

    if not language_supported:
        concern_level = "needs_review"
        status = "limited_language_support"
        summary = (
            "The text language or script is outside the current validated scope. "
            "Any matching English-pattern evidence is partial; do not treat an "
            "absence of matches as evidence of safety."
        )
    elif "protective_credential_warning" in context_codes:
        concern_level = "needs_review"
        status = "protective_warning_context"
        summary = (
            "The text appears to warn against disclosing credentials. This does "
            "not verify the sender or establish that the complete message is safe."
        )
    elif any(item["level"] == "high" for item in evidence):
        concern_level = "high"
        status = "matched_high_concern_combination"
        summary = (
            "One or more higher-concern combinations of requested actions and "
            "context were matched. This is a warning to verify independently, "
            "not proof that the sender or message is fraudulent."
        )
    elif evidence:
        concern_level = "elevated"
        status = "matched_elevated_concern_combination"
        summary = (
            "A combination of contextual indicators warrants extra caution. "
            "Verify through a known official channel before acting."
        )
    elif indicator_codes:
        concern_level = "limited"
        status = "limited_specificity_signals"
        summary = (
            "Only low-specificity text indicators were found. A URL, payment, "
            "UPI, KYC or urgency mention alone does not establish fraud."
        )
    else:
        concern_level = "no_strong_signal"
        status = "no_configured_risk_pattern"
        summary = (
            "No configured higher-concern combination was matched. This does "
            "not mean the message or sender is safe."
        )

    return {
        "engine": "rule_based_evidence_v1",
        "status": status,
        "concern_level": concern_level,
        "review_required": True,
        "evidence": evidence,
        "matched_indicator_codes": [
            code for code in (
                "credential_request",
                "urgency_or_threat",
                "kyc_or_account_update",
                "url_present",
                "upi_context",
                "remote_access_request",
                "payment_request",
            )
            if code in indicator_codes
        ],
        "summary": summary,
        "notice": (
            "This independent English-oriented text-rule assessment does not "
            "replace the ML label, verify a sender or URL, or prove fraud. "
            "Risk-pattern absence is not proof of safety."
        ),
    }
