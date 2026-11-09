# SOUL – Proposed Architecture

**Status:** Design document. The components in this document are proposed; implementation and validation are tracked in ROADMAP.md.

## 1. Design principles

1. **Detect individual events first.** A single suspicious message, URL, QR code or financial-record change must be assessable on its own.
2. **Correlate only when evidence supports it.** Cross-channel correlation is an additional context layer, not a prerequisite for detection.
3. **Be proactive within real platform boundaries.** Use only Android signals available through supported APIs and permissions granted by the user. Provide a user-initiated share/import fallback when automatic access is unavailable.
4. **Explain evidence and uncertainty.** Distinguish a detected indicator, a model prediction and a confirmed fact.
5. **Minimise data.** Collect only what a feature needs, limit retention, protect local/cloud data, and make deletion understandable.
6. **Keep people in control.** SOUL may warn and recommend; it must not initiate payments, change accounts, enter credentials or silently contact family members.

## 2. High-level data flow

~~~mermaid
flowchart TD
    A["Supported event sources"] --> B["Intake adapters"]
    B --> C["Normalisation and sensitive-data minimisation"]
    C --> D["Individual event detectors"]
    D --> E["Event assessment"]
    E --> F["Optional context and correlation"]
    E --> G["Single-event response"]
    F --> H["Incident assessment"]
    H --> I["Verified knowledge retrieval"]
    G --> J["Explanation and safe next steps"]
    I --> J
    J --> K["Android UI / voice / user-approved alert"]
    P["Consent, permissions, access control and audit rules"] -.-> B
    P -.-> C
    P -.-> F
    P -.-> K
~~~

The system should still work when there is only one event. In that case, the correlation step is skipped and the individual event assessment is explained directly.

## 3. Input adapters and realistic access

| Input | Initial approach | Boundary |
|---|---|---|
| SMS | Begin with a controlled test/import workflow; evaluate default-SMS-handler eligibility before any live automatic SMS feature | Ordinary apps do not receive unrestricted SMS access |
| App notifications | Optional Android Notification Listener integration after explicit user approval | Notification text may be hidden, redacted, or unavailable; this is not access to the app's private database |
| URLs | Analyse links received through supported share/browser workflows | Do not silently intercept every link in every app |
| QR codes | SOUL scanner and supported image-import workflow | Decode and inspect the payload; never automatically open a decoded destination |
| Images/screenshots | User-selected import or a supported integration | Do not claim universal visibility into other apps' screens or galleries |
| Audio/calls/video | Future work using user-provided or explicitly supported sources | No covert call recording or unrestricted cross-app capture |
| Financial records | Synthetic records first; later, authorised read-only integrations or user-provided statements | No direct access to a bank's internal Core Banking System |

## 4. Core engines

### 4.1 Individual Communication Risk Engine

Receives a normalised event and returns a structured assessment. A planned result shape:

~~~json
{
  "event_id": "event-demo-001",
  "event_type": "text",
  "risk_level": "medium",
  "risk_score": 0.72,
  "indicators": [
    {
      "name": "urgency_language",
      "description": "The message pressures the recipient to act immediately."
    },
    {
      "name": "unknown_url",
      "description": "The message contains a destination that has not been verified."
    }
  ],
  "limitations": ["This is an automated assessment, not proof of fraud."]
}
~~~

The example is illustrative. A real score must be calibrated on held-out data; do not interpret a raw model probability as certainty.

### 4.2 Financial Account Integrity Engine

The prototype will analyse synthetic or explicitly provided financial records. It may flag anomalies such as:

- A debit that the user does not recognise.
- A balance change that does not reconcile with available transaction rows.
- An FD marked active in one record but closed in a later record.
- A change in maturity or linked-account details when the source records expose the relevant fields.

The first version should use deterministic reconciliation rules and clear audit trails before adding anomaly-detection ML.

A customer-side statement can expose discrepancies, but cannot prove what happened inside a bank. SOUL cannot inspect CBS audit trails or identify employee credential misuse without authorised bank-side data.

### 4.3 Context and incident correlation

An **event** is one observed or submitted item, such as an SMS, URL, QR payload or financial-record change.

An **incident** is a case being investigated. It can contain one event or multiple events. One event is sufficient; correlation is optional.

Potential entities include domains, URLs, sender IDs, phone numbers, UPI IDs, claimed organisations and timestamps. Relationships must record:

- Which two evidence items are linked.
- Which matching attribute supports the link.
- Whether the match is exact, approximate or contextual.
- The time information used.
- The confidence and known limitations.

A common brand name alone must not create a strong connection. Include hard-negative examples during evaluation, such as unrelated items that mention the same bank.

Begin with explainable matching rules and a lightweight graph representation (for example, NetworkX). Consider learned graph methods only after there is enough labelled data.

### 4.4 Verified knowledge retrieval (RAG)

RAG is a supporting knowledge and explanation component; it is not the fraud classifier and it is not the correlation engine.

Planned pipeline:

1. Ingest selected official public guidance.
2. Store source, issuer, publication date, URL, retrieval date and document version.
3. Split documents into meaningful chunks.
4. Generate multilingual embeddings.
5. Retrieve relevant chunks using keyword and vector search.
6. Ask the language model to explain only what the evidence and retrieved documents support.
7. Show citations and abstain when useful evidence is missing.

Potential source categories include regulator guidance, official bank safety pages, telecom advisories and national cybersecurity guidance. Source authenticity and currency must be checked before ingestion.

Treat submitted content and retrieved documents as untrusted data. Do not let instructions inside a message, image, document or retrieved chunk override system rules. Do not place raw private messages or bank statements in a shared knowledge base.

### 4.5 User response layer

The app should give a concise warning, explain the observable indicators, state uncertainty and offer safe next steps. Hindi/Hinglish voice output is planned. High-impact actions must remain user-controlled.

## 5. Suggested data model

| Entity/table | Purpose |
|---|---|
| users | Minimal account and preference information |
| consent_records | Permission and consent state, with timestamps |
| incidents | A user's investigation case; may contain one event |
| events | Normalised metadata for each observed/submitted event |
| evidence_items | References to evidence, with carefully controlled retention |
| extracted_entities | Normalised domains, IDs, sender identifiers and other entities |
| evidence_relations | Explicit, explainable links between items |
| detector_results | Model/rule outputs and model version |
| financial_records | Synthetic or authorised, minimised financial records |
| risk_assessments | Event and incident-level results |
| knowledge_documents | Verified public guidance and provenance metadata |
| user_feedback | User corrections and feedback, with consent |

Do not store passwords, PINs, OTPs, full payment credentials or unnecessary message content. Define retention and deletion behaviour before enabling persistent evidence storage.

## 6. Risk and response semantics

Keep these concepts separate:

- **Indicator:** An observable feature, such as an unfamiliar URL or unusual transaction row.
- **Prediction:** A model's estimate based on its training and evaluation.
- **Correlation:** Evidence that two events may be related.
- **Incident assessment:** The overall assessment of the available evidence.
- **Confirmation:** A conclusion supported by an authoritative source or investigation; SOUL should rarely claim this itself.

Prefer language such as "suspicious", "unusual", "could be related" and "please verify". Avoid declaring a person, account or institution fraudulent without verified grounds.

## 7. Security and privacy controls

- Request permissions only when a feature needs them and explain why.
- Prefer local processing for sensitive data where feasible.
- Encrypt sensitive data in transit and at rest.
- Keep secrets in environment variables or secure platform storage; never commit them.
- Use synthetic test data and redact personal identifiers from logs.
- Apply access control to every user's incidents and evidence.
- Keep audit records for important data access and user-approved actions.
- Provide deletion and consent-revocation paths.
- Defend against prompt injection, poisoned documents, malicious URLs and malformed uploads.
- Do not automatically open links, scan QR destinations in a browser, make payments or perform account changes.

## 8. Non-goals for the first prototype

- Guaranteeing protection from every form of fraud.
- Unrestricted access to other applications.
- Covert call or screen recording.
- Direct access to internal bank systems.
- Automatically blocking accounts or transferring funds.
- Production-grade deepfake detection.
- Claiming that a notification gap proves fraud.
