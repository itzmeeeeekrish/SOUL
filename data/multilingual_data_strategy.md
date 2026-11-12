# SOUL Multilingual Message Data Strategy

**Version:** 0.1  
**Status:** Research and design. No new multilingual candidate has been imported into the training pipeline.

## 1. Why a separate multilingual branch is needed

The prepared Mendeley 2022 working derivative contains 5,797 records. The aggregate script/lexical audit reported:

| Heuristic bucket | Rows |
|---|---:|
| Latin script without selected Hinglish markers | 5,785 |
| Selected Romanized-Hindi lexical signals | 11 |
| Mixed Latin/non-Latin script | 1 |
| Non-Latin-only script | 0 |
| **Total** | **5,797** |

These are heuristic counts, not verified language labels. They do not prove that all 5,785 Latin-script messages are English. The existing baseline therefore remains English-first; it must not be presented as a Hindi/Hinglish classifier.

The original three-class baseline and its held-out test files remain frozen. Multilingual work starts as a separate experiment.

## 2. Initial language scope

Prioritise these three forms first:

1. English.
2. Hindi in Devanagari.
3. Hinglish / Hindi-English code-mixing in Latin script.

Other Indic languages can be considered after the Hindi/Hinglish experiment has a reliable evaluation design.

Do not infer language from script alone. Preserve source-provided language metadata when available, store script separately, and record whether the language tag is publisher-provided, automatically inferred or AI-suggested.

## 3. Candidate-source decisions

### Candidate A — Indian Multilingual Scam & Ham SMS Dataset (14 languages)

- URL: https://huggingface.co/datasets/anmolshrivastav/scam_ham_india_14_languages
- Dataset card declares MIT and is tagged Synthetic.
- 14,000 samples, balanced 7,000 scam / 7,000 ham; 1,000 per language across 14 languages including Hindi and Hinglish.
- Exposed fields: text, binary label and language.
- Its published split is 12,600 train / 1,400 test, stratified by label. The reviewed card does not establish campaign-group separation.

**Planned role:** Candidate for a separate binary multilingual development pilot and script stress-testing, after a local quality/privacy/duplicate audit. Do not equate its two-class target with SOUL's existing three classes. Do not use its pre-made test split as independent real-world evaluation.

### Candidate B — ScamShield Multilingual Smishing & Social Engineering Corpus

- URL: https://huggingface.co/datasets/sidzzz07/scamshield-dataset
- Dataset card declares MIT and describes 85,680 rows in English, Hindi and Hinglish.
- Fields include text, language, source_dataset, is_scam, social-engineering indicators, scam intent, split_group and metadata.
- Viewer examples indicate a mixture of source datasets and synthetic records, including Smishing_Dataset, UCI_SMS_Spam, Indian_Telecom_SMS, Kaggle_Hindi_Merged and Synthetic_Tier_C.
- Some displayed rows use General Spam / Telemarketing as a positive scam-intent class. This risks conflating unwanted promotion and fraud.
- The dataset card does not provide enough source-by-source licence lineage for SOUL to treat the MIT metadata tag as a complete upstream-rights review.

**Planned role:** Hold for full source-lineage, licence, label-semantics, privacy, near-duplicate and split-group audit. The existing local Mendeley and UCI-derived corpora must be checked for overlap before any use. Do not adopt its pre-made test set without inspection.

### Candidate C — Indian Scam SMS (synthetic, audited), 1,580 rows

- URL: https://huggingface.co/datasets/Ridham115/indian-scam-sms-synthetic-audited
- Dataset card declares CC BY 4.0 and reports 797 scam / 783 safe rows in English, Hindi, Hinglish and four regional-English code-mixed styles.
- Every message is LLM-generated. The card says 304 rows were assessed using AI/rules, while 1,350 rows were not individually read; human checking was partial.
- The card explicitly warns that generated domains, provider terms and language quality impose limitations. Google Gemini and Groq-hosted model-provider terms may restrict some uses.

**Planned role:** Possible hard-negative/stress-test supplement only after generator/provider terms are checked. Preserve generator and audit_action fields. Never treat it as real-world data or ground truth.

### Candidate D — Spam SMS in Hindi Language (IEEE DataPort)

- URL: https://doi.org/10.21227/5y8x-n678
- Curator page describes 3,894 Hindi ham/spam messages collected from students' own experiences and those shared by friends/peers, and states that sensitive personal/financial information is not included.
- The actual dataset licence/terms were not visible in the reviewed curator summary.

**Planned role:** Potential real-Hindi evaluation/development source after the actual IEEE DataPort licence and data terms are confirmed. Its ham/spam label semantics do not distinguish promotional spam from scams, so do not map all spam to scam.

### Candidate E — INDICA / IndiF telecom-fraud benchmark

- Repository: https://github.com/nitinc24009/IndiF
- Hugging Face: https://huggingface.co/datasets/vikrant-vikram/INDICA
- Audio + text telecom conversation benchmark across ten Indic languages, rather than SMS-only data.
- Repository displays BSD-2-Clause; dataset-level terms need separate checking. The project notes TTS-generated audio and limited speaker diversity.

**Planned role:** Future voice/call-analysis research, not part of the current SMS message classifier.

Full source notes are in [source_review.md](source_review.md).

## 4. Label compatibility

SOUL's current message classes are:

- legitimate — benign/expected communication.
- spam — unwanted promotion or commercial solicitation without clear deception.
- scam — deceptive communication seeking money, secrets, account access or harmful action.
- needs_review — insufficient evidence; an abstention state, not a training class.

Do not collapse spam into scam merely because an external source uses a binary spam/ham or scam/ham target.

A two-class scam/ham dataset can support a separate binary experiment only if its meaning is preserved. It cannot train the current three-class model without an explicit, justified relabelling rule. A two-class spam/ham source should remain a separate task unless scams can be distinguished with evidence.

## 5. Proposed data pipeline

For every candidate source:

1. Record the dataset URL/DOI, publisher, version, retrieval date, licence, upstream sources and declared generation method.
2. Download into Git-ignored data/raw/; never commit raw data.
3. Inspect file structure and schema before reading all rows.
4. Preserve the original text and source label separately from the model-ready text and SOUL/AI label.
5. Record language, script, source dataset, source record ID, content type, label task, campaign/template group and label provenance.
6. Run blank-row, encoding, language-tag, exact-duplicate, near-duplicate and privacy-pattern audits.
7. Compare against existing Mendeley/UCI-derived rows and any other sources; avoid cross-source leakage.
8. Quarantine conflicting labels and ambiguous rows; AI-generated suggestions remain silver labels.
9. Build a source/campaign/template-group-aware train/validation/test split. Do not trust a publisher split until its grouping method is understood.
10. Keep a source-held-out real-data evaluation set separate from synthetic augmentation.

## 6. Model plan

Keep the historical TF-IDF + Logistic Regression model as the English-first baseline.

For the multilingual branch, compare:
- Character n-gram TF-IDF with Logistic Regression or a linear classifier as a lightweight script-robust baseline.
- A suitable Indic-language pretrained model (for example IndicBERT or MuRIL) only after a source-reviewed language dataset and compute plan exist.

Any model comparison must:
- train on the training partition only;
- use validation for model/threshold selection;
- evaluate the final model once on a separate held-out set;
- report English, Hindi and Hinglish separately, including precision, recall, macro-F1, confusion matrix and false-positive rates;
- report class balance and abstention rate per language;
- include a source-held-out evaluation where possible.

The current API language guard remains in place until a supported language model has been trained and evaluated. Do not remove it just because a text is written in Latin script.

## 7. AI-led annotation policy

Use AI to classify and explain messages in batches, preserving model/provider/version, date, method and rationale. Low-confidence or ambiguous rows become needs_review. The user does not need to manually annotate routine message batches.

AI-generated annotations are silver labels, not independent ground truth. AI suggestions must not be used as an independent test set, and the same model's labels must not be used to claim that model's accuracy. The existing validation/test partitions remain frozen.

The full-dataset annotator requires explicit external-processing opt-in and provider configuration. Do not send masked message text to an external provider until its data-processing and retention terms are approved.

## 8. Immediate next technical step

Audit the 14-language synthetic candidate as a separate pilot before any training:
- verify the actual downloadable file and schema;
- confirm dataset licence metadata and source/generation notes;
- calculate per-language and per-label counts;
- check script-language mismatches, exact duplicates, near-duplicate templates and identifier-like patterns;
- inspect whether the provided 90/10 split leaks similar templates;
- create a new group-safe split if the source is accepted;
- preserve the binary target as binary and keep it separate from the original three-class model.

Only after that audit should SOUL choose whether to run a separate Hindi/Hinglish binary experiment or continue sourcing a three-class multilingual corpus.


## 9. Run the first candidate audit locally

The first candidate audit utility is available at data/audit_multilingual_candidate.py.

It uses the optional Hugging Face Datasets package to download the 14-language synthetic candidate into the local cache. From the active project virtual environment, install the optional package:

    python -m pip install datasets

Then run from the repository root:

    python data/audit_multilingual_candidate.py

The script writes:
- data/private/multilingual_candidates/anmolshrivastav_14lang_candidate_audit.csv — row-level synthetic records with source split, original binary source label, language, script profile, exact-text hash and privacy-candidate flags.
- data/private/multilingual_candidates/anmolshrivastav_14lang_candidate_summary.json — aggregate-only report with class/language/script counts, duplicate and source-split overlap counts, and privacy-pattern totals.

The script does not print messages or IDs, train a model, make a new split, alter the current model, or approve the candidate for use. Keep both outputs local/private. Review aggregate results before deciding whether to build a separate group-safe binary development split.


## 10. Prepare the audited candidate and create a leakage-aware split

After the aggregate audit has completed, run:

    python data/prepare_multilingual_candidate.py

This reads only the local candidate audit CSV and writes:
- data/private/multilingual_candidates/prepared/anmolshrivastav_14lang_prepared.csv — masked model text and provenance fields.
- data/private/multilingual_candidates/prepared/anmolshrivastav_14lang_quarantine.csv — groups whose final masked text has conflicting binary labels.
- data/private/multilingual_candidates/prepared/splits/train.csv
- data/private/multilingual_candidates/prepared/splits/validation.csv
- data/private/multilingual_candidates/prepared/splits/test.csv
- data/private/multilingual_candidates/prepared/anmolshrivastav_14lang_split_summary.json — aggregate counts only.

The script masks candidate URLs/domains, email/UPI patterns, phone/long-number patterns, 12-digit sequences and PAN-like patterns using the existing local SOUL utility. It then groups by the *final masked model text*. If masking causes two different source labels to collapse to the same final text, the whole group is quarantined. Identical final text cannot cross splits.

The split uses StratifiedGroupKFold with 10 folds: one fold for test, one for validation and eight for training (approximately 80/10/10). Stratification is approximate and uses language x source label. The script preserves the original binary scam-vs-ham task and publisher split as provenance; it does not use the publisher test partition as SOUL's test split.

This remains a **synthetic binary development dataset**. A successful split check does not make it real-world data, independent evidence or a three-class SOUL dataset. No model is trained and the original Mendeley baseline/test files remain unchanged.


## 11. ScamShield multilingual corpus — audit candidate only

A second candidate has been identified: https://huggingface.co/datasets/sidzzz07/scamshield-dataset.

The current Hugging Face page reports 85,680 rows and exposes id, text, language, source_dataset, is_scam, head1_social_engineering, head2_scam_intent, split_group and metadata. It lists train, val and test files and displays English, Hindi and Hinglish examples. The dataset card declares MIT, but that top-level declaration is not proof that upstream source data can all be redistributed or reused under MIT. Verify source-specific rights and attribution before redistribution or product use.

**Important semantic issue:** displayed positive examples include the intent General Spam / Telemarketing. This means is_scam=1 must not automatically be interpreted as confirmed fraud or mapped to SOUL's scam label. Preserve source is_scam and head2_scam_intent separately; classify the latter's ambiguous categories before any model experiment.

The audit utility is:

    python data/audit_scamshield_candidate.py

It downloads the candidate into the Hugging Face cache, writes a masked row-level CSV and aggregate JSON only under Git-ignored data/private/scamshield_candidate/, and does not train a model or approve the publisher split. It reports source/language/intent composition, duplicate overlap, split_group integrity, privacy-pattern candidates and source metadata flags. Zero residual regex matches, if observed, is not proof of anonymisation.

**Current status:** audit code and tests committed; local execution and source/licence/label approval pending. No ScamShield rows have been merged into the SOUL training pipeline.


## 12 November 2026 — First ScamShield corpus audit results (local)

- Prepared and masked rows: 85,680. Language counts: English 76,323; Hindi 6,352; Hinglish 3,005.
- Source binary labels: is_scam=0: 54,598; is_scam=1: 31,082.
- The is_scam=1 positives include 24,312 General Spam / Telemarketing records and 6,770 rows with specific scam-intent categories. Do not train directly on the binary source label for SOUL's scam detector.
- Raw exact duplicates: 78 groups, 27 crossing publisher splits, 1 with conflicting binary labels.
- Masked-text duplicate groups: 582, 175 crossing publisher splits, 6 with conflicting labels.
- Publisher split_group values are not generally campaign-level: six of seven source_dataset buckets have one repeated group ID for the entire source. Synthetic_Tier_C has 172 group IDs for 3,720 rows.
- Four rows have residual regex-pattern candidates after masking. They must be excluded/quarantined from any future training/evaluation until the categories and safety are investigated. Zero residual regex matches would not prove complete anonymisation.
- The dataset card declares MIT and lists machine-generated and expert-annotated creators, but per-source upstream reuse rights and label provenance are not established by the card metadata alone.
- A new audit enhancement adds unverified source-ID prefix hints, source-intent-by-source counts, a three-class taxonomy preview (legitimate / spam / scam / needs_review), and residual-pattern counts by source/language. These are diagnostics only; no labels are approved or training performed.
- A separate public implementation using this corpus likewise separates promotional spam from fraud and describes some public-data labels as keyword-assigned/spot-checked. It is a methodological reference, not independent ground truth.
- Local tests and rerun of the enhanced audit are pending.
