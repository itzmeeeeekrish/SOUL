# Multilingual binary baseline — experimental

**Status:** implementation added; local execution and metric results pending.

## Purpose

Train a separate first-pass classifier on the locally prepared 14-language synthetic scam/ham candidate. This experiment is intentionally independent from SOUL's existing three-class Mendeley text baseline.

The target remains the source's binary labels:

- `ham`
- `scam`

These labels are not converted to `legitimate`, `spam` or the existing three-class SOUL labels.

## Fixed model recipe

- Input feature: message text only.
- Vectorizer: character-level TF-IDF.
- Character n-grams: 2–5.
- Minimum document frequency: 2.
- Maximum features: 150,000.
- Sublinear term frequency: enabled.
- Classifier: Logistic Regression.
- Class weights: balanced.
- Maximum iterations: 2,000.
- Random seed: 42.

Character n-grams are a practical first baseline for varied scripts and code-mixed text. This is not a claim that the model understands every language or writing convention.

The `language` field is used only to calculate subgroup metrics. It is not passed into the model. This lets the report show where performance varies without giving the classifier a language label shortcut.

## Input and validation

The training script reads only the prepared local files:

- `data/private/multilingual_candidates/prepared/splits/train.csv`
- `data/private/multilingual_candidates/prepared/splits/validation.csv`
- `data/private/multilingual_candidates/prepared/splits/test.csv`

Before fitting, it checks:
- required columns and non-empty text;
- valid `ham` / `scam` labels and expected partition names;
- recomputed text hashes;
- both classes in each partition;
- no exact masked-text duplicates or group IDs crossing partitions;
- every training language is represented in validation and test.

No row-level message content is printed. The existing Mendeley train/validation/test files and model artifact are not read or modified.

## Evaluation

The script reports:
- accuracy, balanced accuracy, macro F1 and weighted F1;
- per-class precision, recall, F1 and false-positive rate;
- confusion matrix;
- the same core metrics separately for each language;
- per-language ham/scam support counts.

A language subgroup is marked **LOW SUPPORT** if either class has fewer than 20 examples in that evaluation partition. The current prepared split has only 4 Odia scam and 5 Tamil scam examples in the test set, so those subgroup results must be treated as preliminary and not ranked as reliable.

The validation split can be used for later model development. The test split is the initial fixed-recipe holdout only; do not tune features, hyperparameters or thresholds against it. Exact-text grouping prevents exact duplicate leakage, but does not prove campaign-independent generalisation.

## Run

From the active virtual environment, first run the tests from the backend directory:

    cd backend
    python -m pytest -q

Then return to the repository root and run:

    cd ..
    python data/train_multilingual_baseline.py

## Local-only outputs

The script writes:

- `data/private/model_artifacts/multilingual_char_tfidf_logistic_regression.joblib`
- `data/private/model_artifacts/multilingual_baseline_metrics.json`

These artifacts remain under the Git-ignored `data/private/` directory. Joblib uses pickle-based serialization; load only the artifact generated locally from this trusted project code.

## Interpretation limits

- The source candidate is synthetic. Strong scores do not establish real-world scam detection performance.
- This is binary scam/ham classification, not SOUL's three-class message task.
- The source language tags and generated messages may contain errors or unnatural examples.
- Deduplication has reduced Odia and Tamil support, especially for scam messages.
- Per-language metrics are estimates on small held-out samples; support counts must always accompany the scores.
- Regex masking is not proof of anonymisation.
- No result from this experiment should be merged into, or used to replace, the existing Mendeley model or its frozen test results.


## First run results (12 November 2026)
The user successfully ran the initial fixed recipe:

| Metric | Validation | Initial test |
|---|---:|---:|
| Accuracy | 0.9991 | 0.9991 |
| Balanced accuracy | 0.9990 | 0.9990 |
| Macro F1 | 0.9991 | 0.9991 |
| Weighted F1 | 0.9991 | 0.9991 |

The initial test partition contains 1,136 rows and one misclassification. The model has 129,265 character features. Per-language scores are also near-perfect, but Odia (4 scam test examples) and Tamil (5 scam test examples) are low-support estimates.

These results are unusually high for an SMS scam task. The candidate is synthetic and its public examples show clear differences between many ham and scam messages. Template similarity and label-associated synthetic wording must be investigated before drawing further conclusions. These results are not real-world accuracy and do not justify detector integration.

A validation-only diagnostic is now available:

    python data/audit_multilingual_baseline.py

It measures nearest-training-message character-TF-IDF similarity for validation rows and prints top alphabetic model-weighted character fragments. It does not read test rows, retrain or modify the model. Its results are diagnostic evidence only, not proof of leakage or generalisation.


## Similarity diagnostic findings (12 November 2026)
The validation-only nearest-training audit reported:

| Diagnostic | Result |
|---|---:|
| Mean maximum similarity | 0.9062 |
| Median maximum similarity | 0.9512 |
| P90 | 0.9743 |
| P95 | 0.9788 |
| Validation rows with similarity >= 0.90 | 74.2% |
| Validation rows with similarity >= 0.95 | 50.8% |
| Nearest-training label agreement | 99.91% |

No exact group/hash overlap was detected. The very high nearest-neighbour similarity and same-label agreement are consistent with close generated-template or paraphrase families across partitions. They do not prove leakage, but they substantially limit what the near-perfect metric can tell us about generalisation.

The model's strongest character fragments included `url`, `num`, `number`, `upi` and `domain`. The preparation pipeline substitutes regex candidates with explicit placeholders. A further validation-only script now audits these markers by source label and language:

    python data/audit_multilingual_mask_tokens.py

Do not remove or alter markers and then reuse the already-opened test set to compare alternatives. Any ablation or changed preprocessing requires a new experiment/split with a clearly separated evaluation protocol.


## Redaction-marker prevalence audit
A train/validation-only audit found these placeholder rates:

| Marker | Train ham | Train scam | Validation ham | Validation scam |
|---|---:|---:|---:|---:|
| URL | 0.0% | 17.4% | 0.0% | 18.6% |
| DOMAIN | 0.0% | 6.3% | 0.0% | 6.5% |
| LONG_NUMBER | 3.0% | 12.1% | 2.6% | 11.5% |
| 12_DIGIT_NUMBER | 1.3% | 3.6% | 2.5% | 2.6% |
| EMAIL_OR_UPI | 0.0% | 0.0% | 0.0% | 0.0% |
| PAN_LIKE | 0.0% | 0.0% | 0.0% | 0.0% |

These associations repeat across train and validation. The marker categories occur in a subset of scam messages and can be useful shortcuts, but their presence alone does not explain the near-perfect score.

Run the controlled validation-only ablation:

    python data/ablate_multilingual_mask_markers.py

It retrains the same fixed recipe on training text with only the six explicit placeholder tokens removed, then compares validation metrics against the existing saved model on original validation text. It does not read the initial holdout test, overwrite the saved baseline artifact or save an ablation model. This is a diagnostic, not independent evaluation or causal proof.
