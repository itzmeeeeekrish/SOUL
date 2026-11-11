# SOUL Text-Only Baseline — TF-IDF + Logistic Regression

**Status:** First local training and evaluation completed; all 31 backend tests pass. Results below are exploratory dataset results, not real-world fraud-detection accuracy.

## Goal

Create a reproducible first classifier for the three source-derived categories:

- `legitimate` (source `ham`)
- `scam` (source `smishing`)
- `spam` (source `spam`)

This is a dataset development experiment, not a production fraud detector and not a claim that all source labels are perfect.

## Data

The source Mendeley archive is retained locally under the Git-ignored `data/raw/` directory. The redacted preparation output and split files are under Git-ignored `data/private/`. No raw or derived third-party SMS records are committed to the repository.

The first prepared derivative had 5,797 records after exact-text label conflicts were quarantined and same-label exact duplicates collapsed. The split builder then collapsed identical final masked text and quarantined one cross-label masked-text collision:

| Partition | Records | Legitimate | Scam | Spam |
|---|---:|---:|---:|---:|
| Train | 4,004 | 3,383 | 318 | 303 |
| Validation | 856 | 724 | 68 | 64 |
| Test | 861 | 726 | 69 | 66 |
| **Total** | **5,721** | **4,833** | **455** | **433** |

The class distribution is highly imbalanced. A classifier predicting only the majority class would achieve about 84.3% accuracy on this test split while detecting none of the scam or spam examples. Accuracy alone is therefore not a useful success criterion.

## Fixed first model recipe

The first model is fixed before evaluating the held-out test partition:

1. `TfidfVectorizer`
   - Word unigrams and bigrams: `ngram_range=(1, 2)`
   - Ignore terms occurring in fewer than two training messages: `min_df=2`
   - Maximum 50,000 vocabulary features
   - Sublinear term frequency
   - Lowercase normalisation
2. `LogisticRegression`
   - `class_weight="balanced"` to account for class imbalance
   - `max_iter=2000`
   - `random_state=42`

The vectorizer is fitted only on the training text. Validation and test text are transformed using that fitted vocabulary. Only the `text` field is passed to the model; labels are targets. IDs, split names, group IDs, source occurrence counts and source metadata flags are not model features.

**Label provenance note:** The historical baseline target column `label` is the provisional source mapping (`ham → legitimate`, `smishing → scam`, `spam → spam`). The prepared-data workflow now also preserves `source_label` and adds blank human-review fields (`soul_label`, `review_status`, `annotation_note`). This does not change the already-trained baseline, its original split, or its metrics. A future model trained on reviewed SOUL labels must be a separate experiment with a new split and separate metrics.

## Evaluation

The script reports validation and initial held-out test metrics:

- Accuracy and balanced accuracy.
- Macro-F1 and weighted-F1.
- Precision, recall, F1 and one-vs-rest false-positive rate for each class.
- Confusion matrix with rows as actual labels and columns as predicted labels.

The test split is for the fixed initial evaluation only. Do not tune vectorizer settings, model parameters or decision thresholds using test results. Use validation for any later experiment, then preserve the test set for a clearly documented final comparison. Repeatedly checking the test set during development makes it less independent.

## Outputs

Run from the repository root:

```powershell
python data\train_text_baseline.py
```

The model and metrics are written locally under:

- `data/private/model_artifacts/tfidf_logistic_regression.joblib`
- `data/private/model_artifacts/baseline_metrics.json`

These files are Git-ignored. Do not upload model artefacts or private data to GitHub unless a separate release/security review approves it. Joblib is pickle-based: only load the model file created by your own trusted run. Loading an untrusted joblib/pickle file can execute arbitrary code.

## Initial local results (11 November 2026)

The fixed first model recipe was run once locally. The complete backend test suite subsequently passed: 39 passed in 5.16 seconds.

| Metric | Validation | Initial test holdout |
|---|---:|---:|
| Accuracy | 0.9638 | 0.9675 |
| Balanced accuracy | 0.8733 | 0.8920 |
| Macro-F1 | 0.8682 | 0.8915 |
| Weighted-F1 | 0.9634 | 0.9673 |

Per-class test metrics:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Legitimate | 0.9904 | 0.9904 | 0.9904 | 726 |
| Scam | 0.8630 | 0.9130 | 0.8873 | 69 |
| Spam | 0.8226 | 0.7727 | 0.7969 | 66 |

Test confusion matrix (rows = actual; columns = predicted; class order: legitimate, scam, spam):

```text
                 Predicted
Actual          legitimate  scam  spam
legitimate          719       2     5
scam                  0      63     6
spam                  7       8    51
```

The spam class is the main improvement target: 51 of 66 spam messages were correctly identified. Use validation data for error analysis and subsequent experiments. Do not tune on this initial test result. The test split groups exact masked text, not near-duplicate campaigns, and is small for the minority classes.

## Validation-only error analysis

After the baseline has been trained, run this from the repository root:

```powershell
python data\\analyze_baseline_errors.py
```

The script:
- Reads `validation.csv` only; it does not open `test.csv` or retrain the model.
- Checks the validation file's SHA-256 against the metadata saved by the baseline run, so it cannot silently analyse a different split.
- Writes an aggregate report to `data/private/model_artifacts/validation_error_summary.json`.
- Writes the misclassified validation messages to `data/private/model_artifacts/validation_misclassified.csv` for local inspection.

The message-level CSV contains text. Keep it on the local machine, do not commit it, and do not paste its contents into public tools or issues. Regex masking is not guaranteed anonymisation. Share aggregate counts only. The reported top-class probability is a model score, not calibrated confidence.

## Validation-only error analysis (11 November 2026)

The new error-analysis script was run against the saved validation split, and its eight new unit tests are included in the full suite result (39 passed in 5.16 seconds). It verified the validation CSV's SHA-256 against the original baseline metadata. It read no test data and did not retrain the model.

| Validation result | Count |
|---|---:|
| Total | 856 |
| Correct | 825 |
| Misclassified | 31 |
| Accuracy | 0.9638 |

Misclassification pairs (actual → predicted):

| Error pair | Count |
|---|---:|
| Spam → scam | 14 |
| Legitimate → spam | 7 |
| Scam → spam | 5 |
| Spam → legitimate | 5 |

The main observed issue is distinguishing spam from scam: 14 of the 31 errors are spam predicted as scam. This is a hypothesis for local example review, not yet an explanation of why the messages were confused. Inspect the private validation error CSV locally and categorise the likely reasons before changing the model. Do not share message text; share aggregate review categories only. Keep the initial test set untouched.

## Manual review of the 31 validation errors (11 November 2026)

The uploaded validation misclassification CSV was reviewed without reproducing its message text in project documentation. No raw SMS examples are stored in this repository.

| Actual → predicted | Count | Observed pattern |
|---|---:|---|
| Spam → scam | 14 | Prize/free offers, premium-rate calls or subscriptions, reward claims and other paid-message promotions. Strong overlap between the dataset's spam and smishing/scam labels. |
| Legitimate → spam | 7 | Four short or context-poor conversational fragments; two service/contact notifications with promotional wording; one legitimate bank security advisory using security-related terms. |
| Scam → spam | 5 | Promotional or solicitation-style wording (shopping, chat, finance, prize and event offers); the text alone does not make the source's smishing label obvious. |
| Spam → legitimate | 5 | Three neutral, explanatory or service-status messages; two personal-sounding messages that still promote or lead to a paid service. |

### What this suggests

- **19 of 31 errors (61.3%) are between spam and scam.** The strongest current problem is the boundary between those two source-derived classes, not simply missing suspicious language.
- **12 of 31 errors (38.7%) involve legitimate.** Very short messages provide little context; generic conversational language can look like spam, while some spam messages are written in a personal or neutral style.
- The source's `smishing` label was mapped to the project's broader `scam` label. Some examples in that source category look like commercial promotions or paid-service solicitations rather than clearly evidenced phishing. This is a **label-definition / source-annotation ambiguity**, not proof that each source label is wrong.
- The dataset contains older premium-SMS, shortcode, prize-promotion and UK-style commercial message patterns. It is not a representative sample of current Indian scams or multilingual Indian SMS traffic.

### Recommended response before model tuning

1. Keep the current baseline and its initial test evaluation frozen.
2. Clarify the project's annotation rule: distinguish unsolicited promotion/premium-rate spam from deceptive impersonation, credential theft, payment fraud or phishing. Preserve the original source label separately from any SOUL label in future dataset versions.
3. Review or obtain independently human-labelled examples around this boundary before relabelling any examples. Do not automatically relabel the 19 spam/scam confusions.
4. Add hard negative legitimate examples such as short personal chats, bank security advisories and neutral service notifications.
5. Build a privacy-reviewed, campaign-separated and India-relevant evaluation set before making claims about real-world usefulness.

The uploaded CSV was used only for this analysis. It is not copied into the repository. The initial test set remains untouched.

**Prepared-data provenance update (11 November 2026):** The preparation utility now records original `source_label` separately from the provisional `label`, plus blank/pending human-review fields. The regenerated local file passed validation: 5,797 records, all 5,797 pending review, zero invalid mappings or review-state inconsistencies. Full backend suite at that point: 45 passed in 5.25s. The historical baseline split and model remain unchanged.

## Important limitations

- This is an exploratory source-derived baseline, not production validation.
- The split groups exact normalised masked text, not all near-duplicate campaigns. Different variants of a campaign may appear in different partitions.
- Masking uses known regex patterns and is not guaranteed anonymisation.
- Source labels and the provisional mapping require further review; generic `spam` may not always mean promotional content.
- The sample is mostly legitimate English messages and is not representative of Indian multilingual users or modern scam distribution.
- No threshold calibration, probability calibration, drift monitoring, adversarial testing or external campaign holdout is included.
- High recall may increase false alarms; model output must be an advisory signal with reasons and safe next steps, not proof of fraud.

A meaningful next evaluation needs independently sourced, privacy-reviewed, campaign-separated and language-diverse data, plus human-reviewed labels.


## Blinded validation-error review queue

The local helper `data/build_validation_label_review_queue.py` creates a blind review CSV and a separate source/model key for the known validation misclassifications. It verifies the saved validation fingerprint and exact mapping back to the prepared data.

The blind CSV contains message text and blank SOUL review fields, but no source label, provisional label or model prediction. The separate key contains labels and model score but no message text. Review the blind file first; do not open the key until independent labels are complete. The 31 examples were selected because the baseline misclassified them, so this queue is not a representative dataset sample. Both files remain in Git-ignored `data/private/model_artifacts/`. Never commit or share the message-level CSV.
