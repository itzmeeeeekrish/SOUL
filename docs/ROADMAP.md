# SOUL – Development Roadmap

**Current stage:** Milestone 2 – Data and baseline communication detector, with the first local message-analysis API increment implemented. The prepared dataset, grouped split, fixed TF-IDF + Logistic Regression baseline, validation-only error analysis, source-label provenance, AI silver-label pilot and SOUL Master Dataset v1 are documented. The complete backend suite was locally verified after the language-guard changes: **93 passed in 4.95s**, including the AI batch annotator, silver-label exporter, message-analysis API, script guard and language audit tests. The 31-message AI pilot produced 24 provisional labels and 7 abstentions. Manual annotation is not a routine project requirement; AI outputs remain silver labels, not independent ground truth. Source/privacy approval and campaign-independent external validation remain pending. The original baseline test split remains frozen. Milestones 0 and 1 are complete.
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

- [x] Clone the repository locally and create a Python 3.13 virtual environment.
- [x] Pin the initial direct dependencies in backend/requirements.txt.
- [x] Create a minimal FastAPI application.
- [x] Add a /health endpoint.
- [x] Load configuration from environment variables / the local .env file.
- [x] Add a basic automated health-endpoint test.
- [x] Add a placeholder-only .env.example.
- [x] Document setup, run and test commands in backend/README.md.
- [x] Install dependencies and start the API on the local computer.
- [x] Run the automated tests locally and record the passing result (1 passed, no warnings).

**Acceptance met (10 November 2026):** The API started locally, the /health endpoint returned the expected response in a browser, pytest reported 1 passed with no warnings, and the local .env file is ignored by Git. No credentials or actual secrets were added to the repository.

## Milestone 2 – Data and baseline communication detector

- [x] Define a documented dataset schema in `data/dataset_schema.md`.
- [x] Download and structurally inspect the Mendeley 2022 candidate archive; document source, labels, licence and limitations in `data/source_review.md`.
- [x] Locally audit labels, exact duplicates, privacy-pattern candidates and source metadata flags; prepare a redacted derivative under Git-ignored `data/private/` and quarantine conflicting labels.
- [ ] Complete dataset/source approval after privacy, annotation and licence review; do not redistribute raw or prepared third-party messages without a separate permission check.
- [x] Create a synthetic starter dataset v1 (24 rows) and a grouped v2 dataset (84 rows) in `data/synthetic/`.
- [x] Define legitimate, spam and scam labels in `data/annotation_guide.md` and apply them to synthetic examples.
- [x] Assign synthetic v2 campaign groups to train/validation/test in `data/split_strategy.md`; verify that no campaign crosses splits. Real-source/campaign split still requires approved third-party data.
- [x] Build a local preprocessing utility for label mapping, exact-text deduplication, conflict quarantine and candidate-pattern redaction.
- [x] Preserve original `source_label` separately from the historical provisional `label`; add empty `soul_label`, `review_status=pending` and `annotation_note` fields without changing the frozen baseline target.
- [x] Extend prepared-data validation to check source-label mappings and human-review states.
- [x] Regenerate the local prepared CSV with provenance fields, run the validator and full test suite; do not regenerate or alter the frozen baseline split/model.
- [x] Create and validate a deterministic grouped train/validation/test split for the prepared Mendeley candidate; keep identical masked text within one partition.
- [x] Run the fixed text-only TF-IDF + Logistic Regression baseline and record validation/test metrics.
- [x] Report precision, recall, F1, confusion matrix and false-positive rate.
- [x] Run the validation-only error report; inspect masked misclassifications locally and share aggregate counts only (manual reason categorisation remains pending).

**Acceptance:** A repeatable training/evaluation script runs; the test split is not used for training; limitations and class balance are documented. Synthetic v2 validation passed on 10 November 2026. The Mendeley candidate exists only as a local ignored derivative; source/privacy approval remains pending. The grouped 70/15/15 split passed integrity checks. The first ML baseline was trained and evaluated locally, and the latest complete backend suite passes **57 tests in 14.21s**. Metrics and limitations are recorded in `data/model_baseline.md`. Dataset source/privacy approval and external campaign-independent validation remain pending.

| 2026-11-11 | Added and ran the validation-only baseline error-analysis utility; added eight unit tests | Validation: 856 rows, 825 correct, 31 misclassified (accuracy 0.9638). Error pairs: spam → scam 14; legitimate → spam 7; scam → spam 5; spam → legitimate 5. Script verifies the original validation split hash and did not read the test set. Eight focused error-analysis tests and the complete backend suite now pass (39 passed in 5.16s); message-level CSV remains local/private | Clarify source-label vs SOUL-label rules, preserve original source labels, and design a reviewable annotation workflow before any relabelling or model tuning; keep the initial test split frozen |

| 2026-11-11 | Manually reviewed the 31 validation misclassifications from the user-uploaded local report | Spam → scam: 14; legitimate → spam: 7; scam → spam: 5; spam → legitimate: 5. Nineteen errors cross the spam/scam boundary, indicating source-label overlap; 12 involve legitimate messages with short/context-poor or neutral/personal wording. No message content was committed | Clarify annotation definitions and preserve original source labels before model tuning; add reviewed hard negatives; keep the initial test split frozen |

| 2026-11-11 | Added source-label provenance and explicit SOUL review fields to the prepared-data workflow | Preparation output now keeps original `source_label`, retains the old provisional `label` for baseline compatibility, and adds blank `soul_label`, `review_status=pending` and `annotation_note`. Validator/tests check mapping and review-state consistency. Local execution pending | Pull, regenerate `mendeley_prepared.csv`, run its validator and full test suite. Do not overwrite existing split/model artifacts; review labels in a separate future dataset version |

| 2026-11-11 | Regenerated and validated the prepared dataset with source-label provenance fields | 5,797 records; source labels: ham 4,834, smishing 528, spam 435; provisional labels: legitimate 4,834, scam 528, spam 435; all 5,797 review states pending; zero invalid mappings or review-state inconsistencies; residual known regex candidates 0. Full suite: 45 passed in 5.25s. Existing baseline split/model were not regenerated | Generate the blinded 31-error review queue; keep its label/prediction key separate until independent annotation is complete |

| 2026-11-11 | Added a blinded validation label-review queue builder and 12 tests; locally verified the complete test suite on 12 November | Blind file hides source labels and model predictions; separate key contains labels/scores but no message text. Script verifies validation fingerprint and source-provenance mapping. Full local suite: **57 passed in 14.21s**, including the 12 queue tests. Queue-generation script still needs a local run | Run `python data\build_validation_label_review_queue.py`; inspect the blind sheet first and keep both outputs local/private |

- [x] Run the full suite after adding the 12 blinded-review-queue tests: **57 passed in 14.21s** (12 November 2026).

| 2026-11-12 | Completed an assistant-assisted, text-only preliminary assessment of the 31 blind validation errors | Suggested labels: spam 15, legitimate 6, scam 3, needs_review 7. SOUL labels remain blank and review_status remains pending in the delivered suggestion CSV. At that stage the separate model/source key had not yet been inspected; it was later compared against the completed assistant text-only suggestion sheet on 12 November 2026. This error-selected subset is not representative and suggestions are not human ground truth | User/human reviewer should accept, amend or leave each suggestion pending; only then should approved `soul_label` values be recorded. Do not train on assistant suggestions directly or change the frozen baseline |

| 2026-11-12 | Compared the assistant's 31 text-only label suggestions with the uploaded source/model key | All 31 review IDs matched one-to-one. The 31 source-mapped labels were legitimate 7, scam 5, spam 19. Assistant suggestions: legitimate 6, spam 15, scam 3, needs_review 7. Of 24 definitive suggestions, 11 matched the source mapping and 13 differed; 7 were left unresolved. All five source-smishing/scam cases were suggested as spam. The key was opened only after the blind text-only suggestions had been produced. These are advisory suggestions, not human ground truth | Do not relabel automatically. Human adjudication or a second independent reviewer is required; preserve the source/model key and frozen baseline. Investigate the five smishing→spam suggestions and 14 spam→scam errors as separate cases |

| 2026-11-12 | Built SOUL Master Dataset v1 from the uploaded prepared data, baseline splits, quarantines and review files | Master: 5,797 unique prepared records. 5,795 map to existing splits (expanded prepared-record counts: train 4,049; validation 872; test 874); 2 are in one post-redaction split quarantine. Original baseline split files (4,004/856/861 model rows) copied unchanged. Source quarantine: 34 groups / 68 occurrences. 31 validation review IDs joined to 33 prepared rows; uploaded review file marks 24 IDs reviewed and 7 needs_review. All 31 labels match assistant suggestions; 30/31 notes match, so independent human adjudication is not established. Package integrity checks passed; no message-level data committed to GitHub | Keep the package local/private; human-adjudicate assistant-suggestion-derived labels, verify source licence/privacy approval, and run the 12 new blinded-review tests locally before the next code milestone |

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
| 2026-11-10 | Added FastAPI app, /health endpoint, environment configuration, pinned dependencies, test and setup docs; cloned locally, created Python 3.13 venv, started API, verified /health in browser and ran pytest | `python -m pytest -q` → `1 passed in 0.70s`, no warnings; browser health response confirmed | Begin Milestone 2 dataset design |
| 2026-11-10 | Defined schema/annotation guide; added v1 (24 rows) and v2 (84 rows, 21 campaign groups), fixed campaign-aware train/validation/test assignments and updated the validator | Local v1 validation passed earlier; local v2 validation passed: 84 rows, 28 per class, 60/12/12 split, 21 groups, no campaign crosses splits. No third-party dataset imported | Inspect and approve primary three-class data, then deduplicate and privacy-scan before model training |

| 2026-11-11 | Ran the enhanced Mendeley privacy audit; recorded label-wise counts and pattern combinations; added a local masked-review CSV generator | Enhanced local audit: 907/5,971 rows flagged; at least one candidate in 20 ham, 605 smishing and 282 spam rows. 5,064 rows had no candidate. Counts are regex flags, not confirmed PII. Masked-review generator committed but not yet run | Run the masked-review generator locally and inspect the masked candidate rows without sharing the output; report aggregate classifications only |
| 2026-11-11 | Generated the local masked privacy review CSV (907 rows: 20 ham, 605 smishing, 282 spam); added a count-only summary helper and made the masked CSV annotation-ready with spreadsheet formula-prefix protection | Candidate counts exactly match the audit's label-wise "ANY" counts. The masked file remains under Git-ignored `data/private/`; no manual classification or summary run yet | Pull and rerun `python data\\create_masked_privacy_review.py`, classify rows locally in the new manual_review_category column, then run `python data\\summarize_privacy_review.py` and share aggregate counts only |

| 2026-11-11 | Added grouped masked-template privacy review queue and four unit tests | Code and test files committed; unit tests and local queue generation have not yet been run | Pull, run `python data\\build_privacy_review_queue.py`, then run the backend pytest suite and share aggregate counts only |

| 2026-11-11 | Added `data/build_privacy_review_queue.py` to group flagged messages by normalised masked template; added four unit tests | Code and test files verified on GitHub; local queue generation and tests are still pending | Pull, run the grouped queue generator and execute the backend tests; inspect one representative per masked template and prioritise label conflicts/ambiguous cases |

| 2026-11-11 | Ran grouped privacy-review queue and backend tests locally | 5,971 source rows; 907 flagged; 705 unique masked templates; 202 occurrences grouped; 35 masked templates with multiple source labels. Backend pytest: 5 passed in 1.43s. The 35 template collisions are not necessarily the 34 exact-text label conflicts identified earlier | Pull and rerun the enhanced queue and pytest; then filter `has_exact_text_label_conflict=yes` and review only genuine exact-text conflicts locally |

| 2026-11-11 | Enhanced grouped privacy queue to distinguish exact-text label conflicts from different messages merged by masking; expanded unit tests to five cases | Code and tests committed; the earlier local suite was 5 passed before this refinement. Latest version still needs local execution | Pull, rerun the grouped queue, run pytest, then review only groups with `has_exact_text_label_conflict=yes` first |

| 2026-11-11 | Reran the enhanced grouped privacy queue and backend tests after adding exact-text conflict detection | Queue: 5,971 source rows, 907 flagged, 705 masked templates, 202 repeated occurrences grouped, 35 multi-label masked templates, 34 templates containing exact-text conflicts. Earlier raw-text audit: 34 exact conflict groups / 68 rows. Pytest: 6 passed in 1.14s | Preserve the 68 conflicting rows in quarantine; define conservative redaction and duplicate-safe data preparation before training |

| 2026-11-11 | Added local Mendeley preparation utility and seven unit tests | Script reads nested ZIP, maps source labels, quarantines exact-text conflicts, deduplicates same-label messages, masks regex candidates and compares metadata flags. Code/test files verified on GitHub; not yet run locally | Pull, run `python data\\prepare_mendeley_dataset.py` and backend pytest; inspect aggregate output only before deciding on a model split |

| 2026-11-11 | Refined local preparation utility to check source metadata mismatches across every duplicate occurrence and avoid selecting inconsistent metadata arbitrarily | Updated script committed; local execution and the new preparation tests are still pending | Pull latest changes, run the preparation utility, then run full pytest; share aggregate output only |

| 2026-11-11 | Ran local Mendeley preparation and full backend tests | 5,971 source rows; 34 conflicting groups / 68 rows quarantined; 99 same-label duplicate groups / 106 duplicate rows collapsed; 5,797 prepared records. Class counts: 4,834 legitimate, 528 scam, 435 spam. Source-flag mismatches: URL 58, EMAIL 9, PHONE 180; duplicate groups with inconsistent flags: 5, 2, 6 respectively. Pytest: 13 passed in 1.22s | Validate prepared CSV for schema, residual pattern matches, duplicate masked-text collisions and class counts; then design leakage-aware split. First baseline text-only; metadata deferred |

| 2026-11-11 | Added prepared-data validator and five tests | Preparation output previously verified: 5,797 records; classes 4,834/528/435; 68 conflict rows quarantined; backend suite 13 passed. New validator/test files committed but not yet run locally | Run `python data\\validate_prepared_dataset.py`, then full pytest; inspect masked-text collisions before designing the split; use text-only baseline initially |

| 2026-11-11 | Ran prepared-data validator and full backend tests locally | 5,797 records; IDs unique; no blank text/invalid labels/metadata values; 5,903 source occurrences represented; zero residual matches for current regex set; 5,722 unique masked texts; 37 repeated groups / 112 records; 1 cross-label masked-text collision. Pytest: 18 passed in 0.92s | Build deterministic stratified split by final masked text; quarantine cross-label masked-text collision and keep identical model inputs in one partition |

| 2026-11-11 | Added deterministic 70/15/15 stratified split utility and six tests | Groups on final masked text, collapses same-label repeated inputs, quarantines cross-label masked-text groups, uses fixed seed 42 and checks exact text/group separation. Code/tests committed; not yet run locally | Pull, run `python data\\create_mendeley_splits.py` and full pytest; share aggregate split counts only |

| 2026-11-11 | Generated the Mendeley 70/15/15 grouped split and ran the full test suite | 5,797 prepared inputs → 5,722 masked-text groups; 74 duplicate prepared rows collapsed; 2 rows in one cross-label masked group quarantined; 5,721 split rows. Train 4,004; validation 856; test 861. Integrity: no identical text/group crosses splits. Pytest: 24 passed in 1.16s | Install pinned ML requirements, run the fixed text-only TF-IDF + Logistic Regression script, and record validation/test metrics once; do not tune on test |

| 2026-11-11 | Added fixed TF-IDF + Logistic Regression baseline and seven unit tests; pinned scikit-learn 1.9.1 and joblib 1.6.0 | Local training completed; validation macro-F1 0.8682 and test macro-F1 0.8915; full backend suite: 31 passed in 4.54s. Test metrics are initial holdout results only, not for tuning | Use validation-only experiments for error analysis and threshold studies; preserve the initial test set for a later documented comparison |
| 2026-11-11 | Trained the first text-only TF-IDF + Logistic Regression baseline and reran the full backend test suite | Validation: accuracy 0.9638, balanced accuracy 0.8733, macro-F1 0.8682. Initial test holdout: accuracy 0.9675, balanced accuracy 0.8920, macro-F1 0.8915. Test per-class recall: legitimate 0.9904, scam 0.9130, spam 0.7727. Pytest: 31 passed in 4.54s. Model and metrics saved locally under Git-ignored `data/private/model_artifacts/` | Review validation errors and improve spam recall without tuning against the initial test set; obtain campaign-separated and language-diverse evaluation data |

| 2026-11-11 | Verified the validation error-analysis test suite locally | `python -m pytest -q` → 39 passed in 5.16s, including eight new error-analysis tests. Validation analysis is complete and an assistant-generated text-only suggestion sheet has been provided; human adjudication is pending. No message text is stored in GitHub | Refine label definitions and provenance tracking before preparing any revised labels or model experiment |


| 2026-11-12 | Verified all 57 backend tests locally and checked repository privacy hygiene | `python -m pytest -q` → **57 passed in 14.21s**. `git status --short` was empty; `git check-ignore` confirmed the prepared dataset, train split and model artifact are ignored. The blinded review queue generator itself has not yet been confirmed as run. | Generate the two local review-queue files and inspect the blind sheet before opening the separate key; keep all message-level artifacts private |

## 12 November 2026 — AI-led workflow and local message API

- Added an AI annotation policy with explicit silver-label provenance, abstention rules and safeguards against contaminating the frozen validation/test partitions.
- Added a local exporter for the 31-row AI review pilot. It keeps the original source label and official SOUL review fields unchanged; it does not read the separate source/model key.
- Added POST /v1/messages/analyze, which loads only the local TF-IDF + Logistic Regression artifact and returns a provisional text-only suggestion with uncalibrated scores and safe next-step guidance.
- Added tests for the detector, API endpoint, AI silver-label exporter and resumable batch annotator. The complete local backend suite passed **82 tests in 5.05s** on 12 November 2026.
- The AI silver-label pilot contains 7 legitimate, 14 spam, 3 scam and 7 needs_review rows. It is an error-selected sample and must not be used as an independent evaluation set.
- Next: smoke-test POST /v1/messages/analyze against the locally stored model artifact; then decide whether to configure an external AI provider for the opt-in full-dataset silver-label run.

- Added an optional resumable batch annotator for the full prepared dataset. It sends only record_id and text, requires an explicit external-processing flag, records provider/model provenance, converts low self-assessed confidence to needs_review and keeps resumable checkpoints local. No external annotation request has been run.


| 2026-11-12 | Pulled latest AI workflow and endpoint changes and reran the complete backend suite locally | **82 passed in 5.05s**. The earlier malformed CSV test fixture was corrected; the targeted batch-response-ID check is now included in the passing suite. No full-dataset provider calls have been made. | Smoke-test the message-analysis endpoint against the local model artifact; then choose and configure a privacy-appropriate AI provider only if external processing is explicitly approved |


## 12 November 2026 — First live detector smoke test and language guard

- The user successfully called the local `POST /v1/messages/analyze` endpoint against the saved TF-IDF + Logistic Regression artifact. Swagger returned **HTTP 200** and a provisional `scam` candidate for the OTP-threat example. The displayed top model score was 0.6420 and score margin 0.3801; these are uncalibrated model outputs, not fraud probabilities.
- Added a pre-classification script/lexical guard. Devanagari, mixed non-Latin text and a small list of Romanized-Hindi markers now cause the detector to abstain with `needs_review` instead of using the current model.
- Added an aggregate-only language-coverage audit. It prints script/lexical indicator counts only and never outputs message text or IDs.
- Added focused tests for English-like Latin text, Devanagari, Romanized Hinglish, mixed script and audit counts. These new language tests have not yet been run on the user's local environment; rerun the full suite after pulling.
- This is not Hindi/Hinglish model support. The guard is heuristic, and Latin text without a detected marker can still be a non-English language. Do not train or claim multilingual support until language coverage and suitable training/evaluation data are established.
- The user ran the aggregate language audit: 5,797 prepared messages; 5,785 Latin-script rows without selected Hinglish markers; 11 with Romanized-Hindi lexical signals; 1 mixed-script row; 0 non-Latin-only rows. These are heuristic indicators, not language ground truth.
- Next: use this coverage result to plan a sourced, privacy-reviewed Hindi/Hinglish corpus and a campaign-aware language evaluation set without changing the frozen baseline/test set.


| 2026-11-12 | Verified language-aware abstention and audited prepared dataset language/script indicators | **93 passed in 4.95s**. Aggregate audit: 5,797 rows; 5,785 Latin/no selected Romanized-Hindi markers; 11 Romanized-Hindi lexical-signal rows; 1 mixed-script row; 0 non-Latin-only rows. Audit prints counts only. These indicators are heuristic and do not prove language identity. | Build a separately sourced, privacy-reviewed multilingual dataset and evaluate English, Hindi and Hinglish separately; preserve the historical test split |


## 12 November 2026 — Multilingual source review and audit utility

- Reviewed new public candidates for Hindi/Hinglish and broader Indic-language SMS/call text.
- Added a source-by-source risk assessment for a 14-language synthetic scam/ham dataset, an 85,680-row mixed real/synthetic corpus, a 1,580-row AI-generated audited corpus, a Hindi IEEE DataPort dataset with licence still unverified, and the INDICA audio/text call-fraud benchmark.
- Added a multilingual data strategy and provenance-aware schema. The existing Mendeley three-class baseline, split and metrics remain frozen. Binary scam/ham and spam/ham sources must not be silently collapsed into SOUL's legitimate/spam/scam categories.
- Added an aggregate-only importer/auditor for the 14-language synthetic candidate. It preserves publisher source labels, language/script tags, original train/test partition, exact-text hashes and privacy-pattern flags. It does not train a model, create a new split or print message text.
- The previous local full suite passed **93 tests in 4.95s** before this new audit module was added. The 12 new audit tests are pending local verification.
- Next: pull the changes, run the full test suite, install the optional Hugging Face Datasets package, then run the candidate audit. Use its aggregate output to decide whether to create a separate multilingual binary development experiment; do not merge it into the current three-class model.
