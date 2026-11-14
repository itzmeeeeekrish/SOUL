# Safe Message Assessment — Milestone 2.1

**Status:** Implemented as a local development API increment on 14 November 2026. Local test-suite verification is pending after pull.

## What changed

The existing \`POST /v1/messages/analyze\` endpoint now returns four additional fields alongside its existing text-only model suggestion:

- \`risk_indicators\`: category-level keyword matches such as credential-request wording, urgency, KYC/account-update wording, URL presence, remote-access wording and payment wording.
- \`indicator_notice\`: explicitly states that these are simple text-pattern matches, not proof of fraud and not model features.
- \`official_guidance\`: a small set of curated official safety guidance cards selected through transparent keyword rules.
- \`guidance_retrieval_note\`: explicitly describes the retrieval method and its limitations.

The existing classifier, model artifact path and class prediction have not been changed. The current API still loads the historical Mendeley model; the separate ScamShield three-class artifact is not integrated into this endpoint.

## Indicator rules

\`backend/app/services/message_signals.py\` contains conservative regular-expression patterns. It returns category labels and general explanations; it does not echo matching text or raw identifiers.

Current categories:
- \`credential_request\`
- \`urgency_or_threat\`
- \`kyc_or_account_update\`
- \`url_present\`
- \`remote_access_request\`
- \`payment_request\`

A simple negation guard is included for common safety-warning phrasing such as “Never share your OTP”. These rules are not a complete natural-language understanding system. They may miss paraphrases, other languages and context, or flag harmless messages that contain the same terms.

Indicators do not alter or override the machine-learning class. A model prediction and a keyword indicator can disagree; the response exposes both for human review.

## Curated official guidance catalogue

\`backend/app/services/safety_guidance.py\` currently includes paraphrased material from:

1. **RBI — Beware of KYC fraud (Financial Literacy Week 2026):** do not enter KYC details through unknown links; verify the sender; do not share OTP/PIN/password; ignore false urgency.
   - Source: https://www.rbi.org.in/FinancialEducation/FLW2026/English/69656_RBI%20FLW%20KYC%20Fraud%20POSM_Leaflet%20A5.pdf
2. **RBI — Financial Awareness Messages (FAME), fourth edition, February 2024:** never share mobile-banking PIN, internet-banking ID/password or OTP; use trusted banking websites; inform the bank about unusual or unauthorised transactions.
   - Source: https://www.rbi.org.in/commonperson/images/FAME202426022024.pdf
3. **NPCI — UPI FAQ:** do not share UPI PIN; it authorises UPI transactions and bank customer support will not ask for it.
   - Source: https://www.npci.org.in/what-we-do/upi/faqs
4. **Department of Telecommunications — Chakshu:** citizens can report suspected fraud calls, SMS and WhatsApp communications through Sanchar Saathi.
   - Source: https://sancharsaathi.gov.in/
5. **National Cyber Crime Reporting Portal / I4C:** if money has actually been lost or an unauthorised transaction has occurred, contact the bank and report promptly through 1930 or the portal.
   - Source: https://cybercrime.gov.in/

The catalogue records issuer, title, paraphrased advice, URL, source date/description, retrieval date, trigger codes and a relevance reason.

## Important terminology

This is **curated keyword-based guidance retrieval**, not a complete RAG system. It does not yet perform:
- document crawling or scheduled ingestion;
- PDF parsing and chunking;
- embedding generation or vector search;
- LLM answer generation;
- automated citation validation or retrieval evaluation.

These are future milestones. The current result returns pre-reviewed source cards without generating new factual claims.

## Safety and limitations

- Model scores remain uncalibrated outputs, not probabilities of fraud.
- The endpoint remains provisional and \`review_required\` remains true.
- No automatic blocking, deletion, account freezing or payment action exists.
- URL presence is detected, but the URL is not opened, resolved, reputation-checked or verified.
- A keyword match does not establish malicious intent.
- The 1930 guidance is conditional: it applies when financial cyber fraud or an unauthorised debit has actually occurred, not merely because a suspicious SMS was received.
- Devanagari and recognised Romanized-Hindi signals still cause the existing baseline language guard to abstain. Keyword indicators may still be returned, but they are not validated Hindi/Hinglish detection.

## Local verification and demo

After pulling the code, run the complete suite from \`backend/\`:

\`\`\`powershell
python -m pytest -q
\`\`\`

Start the API from \`backend/\`:

\`\`\`powershell
python -m uvicorn app.main:app --reload
\`\`\`

Open http://127.0.0.1:8000/docs and execute \`POST /v1/messages/analyze\` with a synthetic example:

\`\`\`json
{
  "text": "URGENT: Your bank KYC will expire today. Share your OTP immediately at https://example.invalid"
}
\`\`\`

Demonstrate:
1. The model's provisional candidate label and uncalibrated scores.
2. The separate keyword indicators and their explanations.
3. Official guidance cards with issuer and clickable source URL.
4. The explicit notice that indicators are not proof, the URL was not checked, and human review is required.

Use only synthetic demonstration text. Do not send real OTPs, phone numbers, account identifiers or private messages to a public demo.
