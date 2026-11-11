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

The fixed first model recipe was run once locally. The complete backend test suite subsequently passed: 31 passed in 4.54 seconds.

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

## Important limitations

- This is an exploratory source-derived baseline, not production validation.
- The split groups exact normalised masked text, not all near-duplicate campaigns. Different variants of a campaign may appear in different partitions.
- Masking uses known regex patterns and is not guaranteed anonymisation.
- Source labels and the provisional mapping require further review; generic `spam` may not always mean promotional content.
- The sample is mostly legitimate English messages and is not representative of Indian multilingual users or modern scam distribution.
- No threshold calibration, probability calibration, drift monitoring, adversarial testing or external campaign holdout is included.
- High recall may increase false alarms; model output must be an advisory signal with reasons and safe next steps, not proof of fraud.

A meaningful next evaluation needs independently sourced, privacy-reviewed, campaign-separated and language-diverse data, plus human-reviewed labels.
