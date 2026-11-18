# Safe Message Assessment — Milestone 2.1

**Status:** Implemented as a local development API increment. The user reported 265 passing backend tests on 18 November 2026 after the protective-warning safeguard; subsequent benchmark evaluator tests require a new full-suite run.

## What changed

The existing \`POST /v1/messages/analyze\` endpoint now returns four additional fields alongside its existing text-only model suggestion:

- \`risk_indicators\`: category-level keyword matches such as credential-request wording, urgency, KYC/account-update wording, URL presence, UPI context, remote-access wording and payment wording.
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

A simple negation guard is included for common safety-warning phrasing such as “Never share your OTP”. A separate narrow protective-warning pattern identifies a standalone warning not to disclose credentials. It is emitted as a context flag only when no other configured risk indicator matched. In that case, the API withholds its final model candidate and returns `needs_review`; the underlying model candidate and scores are retained only as debug fields. If other indicators are present, normal provisional model behaviour continues. This guard is not a complete natural-language understanding system and could miss paraphrases or misread mixed/contradictory context.

Indicators do not normally change the machine-learning class. The protective-warning abstention is a distinct, deliberately conservative exception: it does not label the message legitimate, and it still requires human review.

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
- The protective-warning rule is narrow, heuristic and only triggers when no other configured risk indicators matched. It is not proof of legitimacy; it only changes the final API output to `needs_review`.
- The raw model candidate and scores may still be wrong and remain uncalibrated; they are exposed for debugging, not as a fraud probability.
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
1. The suspicious KYC example's provisional candidate label, uncalibrated scores, text indicators and official guidance.
2. The “Never share your OTP” hard negative: SOUL should return `needs_review`, show a protective context flag, and retain the raw model candidate only for debugging.
3. The Devanagari example's unsupported-language abstention.
4. The explicit notice that indicators are not proof, the URL was not checked, scores are not fraud probabilities, and human review is required.

Use only synthetic demonstration text. A repeatable three-case runner is available at `backend/demo_safe_message_assessment.ps1`. Do not send real OTPs, phone numbers, account identifiers or private messages to a public demo.


## Independent risk evidence layer — 18 November 2026

**Status:** Implemented in the repository; local Windows verification is pending.

The API now returns a separate `risk_assessment` object from `backend/app/services/risk_assessment.py`. It is deliberately independent of the ML classifier: the engine does not overwrite `candidate_label`, `model_candidate_label` or model scores.

The response contains:
- `engine`: rule-set version identifier.
- `status`: why the rule engine produced its advisory status.
- `concern_level`: `high`, `elevated`, `limited`, `no_strong_signal` or `needs_review`.
- `evidence`: category-level rule IDs, levels, titles and explanations. Matched message fragments and URLs are not echoed.
- `matched_indicator_codes`: the existing low-level signal categories.
- `summary` and `notice`: user-facing explanation and limitations.

### Higher-concern combinations

The first rules look for:
- a request to disclose a credential;
- remote-access wording combined with financial context;
- a payment request combined with authority, delivery or essential-service pressure **and an additional escalation signal** (a URL in the message, explicit urgency language, or a serious legal/authority threat);
- a new-number family identity claim combined with a transfer request and discouragement of independent contact;
- an upfront fee linked to a job or promised benefit.

A routine utility reminder that mentions a due date, late fee or possible service disconnection is not high concern by itself; the payment-pressure rule requires an additional escalation signal. An urgent KYC/account-update message with a URL is marked elevated, not automatically treated as a confirmed scam. A URL, payment word, KYC mention, UPI reference or urgency phrase alone can only produce a limited signal, not a high-concern result.

Unsupported-language cases remain `needs_review`; English-oriented keyword rules are not treated as validated Hindi/Hinglish analysis. Protective-warning context also remains `needs_review`.

### Non-negotiable safety boundaries

- A `high` concern level means a configured combination warrants strong caution; it is **not** a fraud verdict or probability.
- `no_strong_signal` does **not** mean the sender or message is safe.
- Every result still requires independent verification and human judgement.
- The engine does not inspect a URL, sender identity, transaction, phone call, app or device.
- Rule coverage is English-oriented and finite. Paraphrases, obfuscation and other languages may be missed.
- The ML label and the independent risk assessment must be read together; neither is proof by itself.

### Regression coverage

`backend/tests/test_risk_assessment.py` covers the known synthetic scam patterns from benchmark v1 and benign lookalikes, including routine KYC, payment receipts, salary notifications, promotions, URL-only messages and protective warnings. The fixed `data/synthetic/message_evaluation_v1.csv`, its expected labels, the trained model and the original Mendeley test partition are unchanged.

After pulling, run `python -m pytest -q` from `backend/`. Inspect `risk_assessment` in the existing Swagger endpoint at `POST /v1/messages/analyze`. Local verification has not yet been reported.


### User-facing guidance precedence

The ML `candidate_label` and scores remain unchanged, but the top-level `guidance` now follows the independent evidence layer when it reports `high` or `elevated` concern. This prevents a contradictory benign-sounding message when the classifier predicts `legitimate` but the separate rule engine has found a stronger warning combination. Low-specificity or no-signal cases continue to use the model-category guidance; unsupported-language and protective-warning branches retain their dedicated review guidance. The risk message remains precautionary, not a fraud verdict.


### Model/evidence disagreement on benign-looking messages

A routine KYC reminder can still receive an ML `scam` suggestion because the historical text classifier has false positives. When the ML suggests `scam` but the independent rules find only `limited` or `no_strong_signal` evidence, the top-level guidance now explicitly describes the disagreement. It keeps the ML suggestion visible, says that the disagreement does not prove fraud, and recommends independent verification rather than presenting a definitive deceptive-request warning. This is a user-guidance safeguard, not a model correction or a new accuracy result.
