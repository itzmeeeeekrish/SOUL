# SOUL Label Review Protocol

**Version:** 1.0  
**Status:** AI-led silver-label workflow; manual annotation is not required for routine project progress.

## Current policy

SOUL uses AI-assisted text review to create provisional message labels and identify uncertain cases. AI-generated labels are treated as **silver labels**, not independently verified ground truth. This lets development proceed without asking the user to manually classify individual messages.

The complete workflow, label definitions, provenance rules, privacy constraints and limitations are documented in [ai_annotation_policy.md](ai_annotation_policy.md).

## Preserve source and AI labels separately

| Field | Meaning |
|---|---|
| source_label | Original publisher category, unchanged |
| label | Provisional mapping used by the frozen historical baseline |
| soul_label | Reserved for separately adjudicated labels; do not fill it with AI output |
| review_status | Existing independent-review state; AI must not change it |
| ai_suggested_label | AI label: legitimate, spam, scam or needs_review |
| ai_annotation_status | provisional or needs_review |
| ai_annotation_note | AI's text-based rationale and uncertainty |
| ai_annotator / ai_model / ai_method | Annotation provenance |

Never overwrite the original source label or the historical baseline target. Do not turn AI output into human-reviewed ground truth.

## Current 31-message pilot

The error-focused pilot has 31 messages. The AI assessment produced 7 legitimate, 14 spam, 3 scam and 7 needs_review suggestions. This subset was selected because the baseline misclassified these messages; its class counts are not representative of the full dataset.

Among the 24 non-abstained suggestions, 14 match the original source-label mapping and 9 match the baseline model prediction. The source mapping, baseline and AI assessment can all be wrong. This comparison is diagnostic only.

## Rebuild the local AI silver-label file

The assistant suggestion sidecar must be saved locally as:

    data/private/model_artifacts/validation_label_ai_suggestions_sidecar.csv

The blind validation queue remains:

    data/private/model_artifacts/validation_label_review_blind.csv

Run from the repository root:

    python data/build_ai_validation_review_dataset.py

The script writes:

    data/private/model_artifacts/validation_label_review_ai_silver.csv

It joins by review_id, checks for missing/duplicate IDs and invalid label/status pairs, neutralises formula-like CSV text, and preserves the official review fields as blank/pending. It deliberately does not read the separate source/model key. All message-level files stay local/private and Git-ignored.

## Model and evaluation safeguards

- The original train/validation/test partitions, baseline artifact and initial test metrics remain frozen.
- Do not add AI-labelled validation or test messages to training and then reuse them as an independent evaluation.
- A future AI-labelled training corpus must be a new version with its own group-aware split and separate metrics.
- Keep needs_review messages out of ordinary supervised training.
- Record AI model, method, date and rationale. Do not claim human verification.
- AI suggestions must not independently trigger account freezes, payment blocks or accusations.

## Historical compatibility

The first baseline maps the publisher labels as ham to legitimate, smishing to scam and spam to spam. This historical mapping remains unchanged for reproducibility. The AI labels are generated from message text and may differ. The difference is a reason for further analysis, not automatic proof that either label is correct.

## Privacy

The prepared text uses pattern-based masking, which is not guaranteed anonymisation. Keep raw data, prepared messages, AI outputs, review files, partitions and joblib model files outside Git. Do not send the entire prepared dataset to an external model provider without a separate privacy and data-processing assessment.
