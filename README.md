# SOUL

**A privacy-first digital and financial safety intelligence assistant.**

SOUL is a proposed Android-first assistant intended to help people—especially elderly and less technically confident smartphone users—recognise suspicious digital activity, understand the evidence, and take safer next steps.

> **Project status: Milestones 0 and 1 complete; Milestone 2 dataset preparation is in progress**
>
> The project includes design documentation, a locally verified FastAPI backend foundation, and the first dataset-design increment. The health endpoint and automated test passed (1 passed, no warnings) on 10 November 2026. The starter message dataset is synthetic only; a trained detector and the financial-integrity, RAG and Android features are not implemented yet.

## The problem

Digital fraud does not happen through one channel alone. People may encounter suspicious SMS messages, app notifications, links, QR codes, fake payment screenshots, impersonation attempts, or unexpected changes in their financial records.

Many tools inspect one item at a time. SOUL aims to combine:

1. **Proactive detection where Android makes the data available and the user has granted the required permission.**
2. **Individual risk analysis**, so one suspicious message or transaction can be investigated on its own.
3. **Contextual intelligence**, which can connect multiple events only when the available evidence supports a relationship.
4. **Clear and accessible guidance**, including simple Hindi/Hinglish explanations and verified safety instructions.
5. **Privacy and user control**, rather than unrestricted collection of personal data.

## What SOUL is intended to do

### 1. Communication risk detection

Analyse supported digital signals such as:

- Suspicious SMS or notification text.
- URLs and potentially phishing websites.
- QR-code destinations.
- User-provided screenshots or images through supported workflows.

Each item should be assessed independently first. A single suspicious item can be enough to create a case and trigger a warning.

### 2. Context and incident intelligence

An *incident* is simply a case SOUL is investigating. It may contain only one suspicious event or several related events.

When multiple events exist, SOUL may compare identifiers and context—such as a domain, sender, phone number, UPI ID, claimed organisation, or event timing—to determine whether there is evidence that they are connected.

A shared name or keyword alone is not proof of a connection. SOUL should show why it linked evidence and preserve uncertainty when the relationship is unclear.

### 3. Financial account integrity monitoring

SOUL is also intended to help users notice unexpected changes in financial records, such as:

- Unrecognised debits or credits.
- Unexpected changes in balances.
- Fixed-deposit closure or maturity discrepancies.
- Other unusual changes visible in records the user has authorised SOUL to process.

The initial prototype will use synthetic records and/or user-provided sample statements. Live bank or Account Aggregator integrations are future work and must use authorised, consent-based access. SOUL cannot inspect a bank's internal Core Banking System or prove employee misconduct from customer-side records.

### 4. Verified safety guidance with RAG

A Retrieval-Augmented Generation (RAG) component is planned to retrieve relevant information from traceable, trusted sources—such as official regulator, bank, telecom and cybersecurity guidance.

The detection engine decides what signals are suspicious. RAG supplies relevant knowledge and procedures; it does not independently prove that fraud occurred.

### 5. Voice-first, accessible assistance

The intended experience includes simple Hindi/Hinglish explanations, voice output, clear warnings, and optional trusted-family escalation with the user's consent.


## Current dataset-design starter\n\nThe dataset foundation includes a documented schema, three annotation labels, a public-source review, 24 v1 and 84 grouped v2 synthetic SMS examples, a campaign split strategy and a CSV validator. From the repository root, run `python data/validate_dataset.py`. See [data/dataset_schema.md](data/dataset_schema.md), [data/annotation_guide.md](data/annotation_guide.md), [data/source_review.md](data/source_review.md), [data/split_strategy.md](data/split_strategy.md) and [data/synthetic/sms_messages_v2.csv](data/synthetic/sms_messages_v2.csv). Third-party datasets have not been imported.\n\n## Current backend starter

The first backend increment includes a FastAPI application, environment-based configuration, a GET /health endpoint, one automated test, pinned direct dependencies and a placeholder .env.example.

Follow [backend/README.md](backend/README.md) to recreate the local Python environment, start the API and run tests. The first local verification has passed; repeat these steps on a new setup.

## Proposed architecture

```mermaid
flowchart TD
    A["Supported Android events and authorised financial records"] --> B["Input processing and data minimisation"]
    B --> C["Communication Risk Engine"]
    B --> D["Financial Integrity Engine"]
    C --> E["Individual event assessment"]
    D --> E
    E --> F["Context and incident correlation (when evidence exists)"]
    F --> G["Verified knowledge retrieval (RAG)"]
    G --> H["Risk explanation and recommended next steps"]
    H --> I["Android interface, voice guidance and optional family alert"]
    J["Consent, privacy, access control and auditability"] -. governs .-> B
    J -. governs .-> F
    J -. governs .-> I
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design details and implementation boundaries.

## Planned technology stack

The stack below is a **proposal**. Tools will be introduced only when the relevant milestone begins.

| Area | Planned technology | Intended role |
|---|---|---|
| Android | Kotlin, Android SDK, Jetpack Compose | Mobile application and supported device integrations |
| Backend | Python, FastAPI | API layer and orchestration |
| Classical ML | Scikit-learn | Baseline message classifier |
| NLP | Hugging Face Transformers | Multilingual text classification experiments |
| Image / QR | ML Kit and/or OpenCV | Supported OCR, image and QR processing |
| Correlation | NetworkX initially | Explainable entity and event relationships |
| Database | PostgreSQL | Incidents, evidence metadata and analysis results |
| RAG retrieval | PostgreSQL full-text search + pgvector | Keyword and vector retrieval over verified documents |
| Voice | Android Text-to-Speech; speech input evaluated separately | Accessible voice interaction |
| Testing | Pytest and Android tests | Automated checks and regression tests |

## Important scope and safety boundaries

SOUL is a defensive assistant, not a bank, antivirus replacement, law-enforcement system, or guarantee against fraud.

- Android does not provide unrestricted access to every other app's private content. Automatic monitoring must use supported APIs, user-granted permissions and applicable platform policies.
- User-initiated sharing or import is a fallback when automatic access is unavailable—not a reason to request excessive permissions.
- Bank statements, notifications and other customer-side records can reveal anomalies, but cannot expose all internal bank activity. SOUL must not claim to detect internal staff credential misuse without authorised bank-side evidence.
- A screenshot is not proof that a payment succeeded. The bank or payment provider's authorised record is the source of truth.
- A suspicious indicator is not proof of fraud. Risk explanations must communicate uncertainty and avoid unsupported accusations.
- Do not commit real personal messages, bank statements, account numbers, phone numbers, credentials, API keys or other sensitive information. Use synthetic or properly anonymised examples.
- No financial transaction, account change, or message is to be executed automatically by SOUL.

## Development roadmap

1. **Project foundation:** documentation, repository structure and development environment.
2. **Backend foundation:** FastAPI application, configuration, health endpoint and tests.
3. **Data and baseline detection:** curated/synthetic examples, preprocessing and a baseline classifier.
4. **Evidence processing:** supported URL, QR and image workflows.
5. **Incident intelligence:** entity extraction, explainable correlation and case history.
6. **Financial integrity prototype:** synthetic statement and FD-record analysis.
7. **RAG:** verified document ingestion, retrieval, citations and abstention.
8. **Android integration:** user interface, supported monitoring, voice guidance and permissions.
9. **Evaluation:** compare baselines, measure false positives, test privacy and usability, and document limitations.

Track detailed work in [docs/ROADMAP.md](docs/ROADMAP.md).

## Current repository structure

```text
SOUL/
├── README.md
├── .gitignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── LEARNING_NOTES.md
├── backend/
├── ml/
├── rag/
├── android/
└── research/
```

Folders for implementation will be added as their milestones begin.

## Learning and contribution approach

This is also a learning project. Each module should include:

- A simple explanation of the problem and design.
- Small, understandable implementation steps.
- Tests or a reproducible manual test.
- Notes on limitations and security.
- Short Hinglish revision notes and likely viva questions.

See [docs/LEARNING_NOTES.md](docs/LEARNING_NOTES.md).

## Disclaimer

SOUL is an educational project and prototype under development. It must not be relied on as the sole basis for financial or security decisions. Users should verify suspicious activity directly through official bank, telecom or government channels.
