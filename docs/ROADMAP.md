# SOUL – Development Roadmap

**Current stage:** Repository foundation.  
**Working rule:** Build small, testable increments. Do not mark a feature complete until its acceptance criteria have been checked and the work is documented.

## Product objective

Build an Android-first, privacy-conscious assistant that assesses individual suspicious digital events, optionally connects related evidence, analyses authorised financial records for anomalies, and explains safe next steps using verified knowledge.

A single event can be an incident. Cross-channel correlation is optional context, not a requirement for detection.

## Milestone 0 – Repository foundation

- [x] Create public GitHub repository.
- [x] Add initial README.
- [x] Add architecture, roadmap and learning documentation.
- [x] Add Python/Android ignore rules.
- [x] Agree on development workflow and commit conventions.

**Acceptance:** A newcomer can understand the project goal, boundaries, proposed architecture and next milestone from the repository.

## Milestone 1 – Backend foundation

- [ ] Create Python virtual environment and pin dependencies.
- [ ] Create a minimal FastAPI application.
- [ ] Add a health-check endpoint.
- [ ] Add configuration through environment variables.
- [ ] Add basic automated tests and instructions to run them.
- [ ] Add a .env.example containing placeholder values only.

**Acceptance:** The API starts locally, the health endpoint returns the expected response, tests pass, and no secrets are committed.

## Milestone 2 – Data and baseline communication detector

- [ ] Define a documented dataset schema.
- [ ] Identify permitted, traceable data sources and licensing/usage conditions.
- [ ] Create a small synthetic starter dataset for development.
- [ ] Label legitimate, spam and scam examples with a clear annotation guide.
- [ ] Split by source/campaign where possible to reduce data leakage.
- [ ] Build preprocessing and a TF-IDF + Logistic Regression baseline.
- [ ] Report precision, recall, F1, confusion matrix and false-positive rate.

**Acceptance:** A repeatable training/evaluation script runs; the test split is not used for training; limitations and class balance are documented.

## Milestone 3 – Supported evidence processing

- [ ] Implement URL parsing and safe canonicalisation.
- [ ] Add QR decoding in a controlled workflow.
- [ ] Add OCR for user-selected images/screenshots.
- [ ] Validate file type, size and malformed inputs.
- [ ] Ensure decoded URLs are analysed, never automatically opened.
- [ ] Add tests for benign, suspicious and malformed examples.

**Acceptance:** Each input type returns structured data and a clear, testable assessment. The app does not claim access to content it cannot observe.

## Milestone 4 – Individual event assessment and incident model

- [ ] Define event and incident schemas.
- [ ] Allow an incident to contain exactly one event.
- [ ] Store detector outputs with model/version and timestamps.
- [ ] Produce an explainable event-level risk result.
- [ ] Add controlled incident history and deletion behaviour.

**Acceptance:** One suspicious event can be assessed and shown as a standalone incident.

## Milestone 5 – Cross-channel correlation

- [ ] Extract and normalise selected entities.
- [ ] Define explicit relationship types and provenance.
- [ ] Implement explainable exact-match rules first.
- [ ] Add time-aware context without assuming causation.
- [ ] Include unrelated hard-negative examples.
- [ ] Compare independent detection with correlation-assisted assessment.
- [ ] Measure relationship precision/recall and incident-level precision/recall.

**Acceptance:** Every proposed link can be traced to supporting evidence; unrelated events are not automatically grouped; correlation can be skipped when evidence is insufficient.

## Milestone 6 – Financial account integrity prototype

- [ ] Define a synthetic bank statement and FD-record schema.
- [ ] Parse sample CSV/PDF-derived structured records (no real customer data in Git).
- [ ] Reconcile opening balance, credits, debits and closing balance where fields permit.
- [ ] Flag unrecognised or unexplained transaction patterns for user review.
- [ ] Compare expected FD state with a later authorised/sample record.
- [ ] Add tests for missing rows, duplicates, reversals and legitimate unusual activity.
- [ ] Document that customer-side records do not expose internal bank audit logs.

**Acceptance:** The prototype explains the exact rows and rules behind each anomaly and does not claim to prove fraud.

## Milestone 7 – RAG knowledge engine

- [ ] Select a small set of official public guidance sources.
- [ ] Record issuer, URL, publication date, retrieval date and version.
- [ ] Build ingestion, chunking and retrieval.
- [ ] Add keyword + vector retrieval.
- [ ] Return source-linked answers.
- [ ] Test citation correctness, relevance and unsupported-claim rate.
- [ ] Add abstention when no relevant source is retrieved.
- [ ] Test prompt injection in submitted and retrieved content.

**Acceptance:** Answers display traceable sources and can decline to answer when evidence is insufficient.

## Milestone 8 – Android application and supported monitoring

- [ ] Create the Kotlin/Jetpack Compose application.
- [ ] Build an incident and warning screen.
- [ ] Implement a user-initiated share/import fallback.
- [ ] Evaluate the permitted Android integration for each data source.
- [ ] Request permissions just in time with clear explanations.
- [ ] Add Hindi/Hinglish text-to-speech.
- [ ] Add notification settings, consent review and deletion controls.
- [ ] Test on real devices and document unsupported cases.

**Acceptance:** Only supported signals are monitored; permission denial does not break unrelated functionality; the user can see and control monitoring.

## Milestone 9 – Evaluation and demonstration

- [ ] Compare baseline and correlation-assisted models.
- [ ] Report precision, recall, F1, false positives and latency.
- [ ] Evaluate RAG retrieval and citation correctness.
- [ ] Run usability tasks with informed consent.
- [ ] Document device/Android version and permission limitations.
- [ ] Prepare reproducible demo scenarios using synthetic data.
- [ ] Write final technical report and viva notes.

**Acceptance:** Results are reproducible, claims match evidence, and all known limitations are presented honestly.

## Prioritisation

For the first working prototype, prioritise:

1. Backend and clean data schemas.
2. One individual-event detector.
3. One-event incident record.
4. QR/URL or screenshot workflow.
5. Explainable correlation as a later layer.
6. Synthetic financial-record reconciliation.
7. RAG only after detection and evidence structures are stable.

Do not start with live banking integrations, unrestricted background monitoring, live call interception or deepfake video detection.

## Progress log

Update this section after each meaningful development session.

| Date | Work completed | Tests/evidence | Next step |
|---|---|---|---|
| 2026-11-09 | Created repository, expanded README, added architecture, roadmap, Hinglish learning notes and ignore rules | Documentation files verified on GitHub; application tests not applicable yet | Begin backend foundation |
