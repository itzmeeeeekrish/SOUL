# SOUL AI-Assisted Annotation Policy

**Version:** 1.0  
**Status:** Active development policy for AI-generated silver labels.

## Purpose

SOUL uses an AI-led workflow for reviewing ambiguous message data. Manual review of every row is not a project requirement. AI can prepare provisional labels, explain the text evidence, identify uncertainty and produce repeatable review artifacts.

AI-generated labels are **silver labels**, not independently verified ground truth. This distinction protects the evaluation process without requiring the user to label thousands of messages manually.

## Label definitions

- **legitimate:** The text appears to be ordinary, expected or benign communication, with no clear deceptive request or unwanted promotional intent.
- **spam:** The text appears to be unsolicited promotion, bulk marketing or unwanted commercial solicitation, without clear deception to obtain money, credentials, account access or device control.
- **scam:** The text appears designed to deceive or manipulate the recipient into sending money, revealing secrets, granting account access, approving a payment or taking another harmful action.
- **needs_review:** The available text does not provide enough evidence for a defensible class. This is an abstention state, not a fourth training class.

A URL, bank name, unknown sender, prize, urgency or poor grammar alone is not enough to label a message as a scam. Focus on the claim, context and requested action. A promotion can be spam without being fraud.

## Provenance: never overwrite the source

Keep these concepts separate:

| Field | Meaning |
|---|---|
| source_label | Original publisher label, unchanged |
| label | Historical source-to-SOUL mapping used by the frozen first baseline |
| soul_label | Reserved for separately adjudicated SOUL ground-truth labels; AI must not fill it |
| review_status | Existing human-review state; AI must not change it |
| ai_suggested_label | AI-proposed class or needs_review |
| ai_annotation_status | provisional or needs_review |
| ai_annotation_note | Text-only evidence and uncertainty explanation |
| ai_annotator | Assistant/provider name |
| ai_model | Exact model name/version when known |
| ai_method | Text-only, multimodal, rule-assisted, or other method |
| ai_created_date | Date the AI annotation was produced |

The current 31-row review export keeps the official fields unchanged and stores AI output in separate columns. The local exporter intentionally does not read the separate source/model key.

## AI decision procedure

1. Read the complete message text, including its wording and requested action.
2. Identify any claimed identity, reason for contact and requested action.
3. Look for direct evidence of deception, impersonation, credential collection, payment manipulation or device compromise.
4. Use spam when the text is promotional/unwanted but does not show a deceptive attempt.
5. Use legitimate when the text appears benign and no harmful request is evident.
6. Use needs_review when critical context is absent or intent cannot be established from text alone.
7. Record a concise rationale. Do not invent sender details, URL reputation, transaction context or external verification that was not inspected.

For multimodal or cross-channel cases, each signal must retain its own source and analysis method. A relationship between two events must be supported by matching evidence; common words or brand names alone are not enough.

## Current 31-message AI pilot

The current error-focused pilot contains 31 messages selected because the baseline misclassified them. AI assigned 24 provisional labels and abstained on 7:

| AI suggestion | Count |
|---|---:|
| legitimate | 7 |
| spam | 14 |
| scam | 3 |
| needs_review | 7 |

In the 24 non-abstained suggestions, 14 agree with the original source-label mapping and 9 agree with the baseline model prediction. These are comparisons between two imperfect sources, not AI accuracy, model accuracy or ground truth. The 31 cases are deliberately error-selected and do not represent the full dataset.

## How AI labels may be used

- Use the AI pilot as a local silver-label artifact for error analysis and controlled development experiments.
- Preserve every AI label, rationale, model identifier and method in separate fields.
- Keep needs_review rows out of ordinary supervised training unless a later explicit policy defines how to use them.
- Do not use AI labels from the original validation or test partitions to train a model and then report those same records as independent evaluation.
- The original train/validation/test files, historical model artifact and first test metrics remain frozen.
- A future AI-labelled training dataset must have a new version, a new leakage-aware split, separate metrics and a clear record of how labels were generated.
- Never present AI labels as human-verified, regulator-approved or proof that a sender committed fraud.

## Privacy and data handling

- The existing prepared text was masked using known patterns; this does not guarantee anonymisation.
- Keep raw data, prepared messages, AI outputs, review queues, splits and model artifacts in Git-ignored local folders.
- Do not send the full prepared dataset to an external model provider until the data-processing, privacy and provider-retention implications have been assessed.
- Use only trusted local joblib artifacts; joblib is pickle-based and loading an untrusted file can execute code.
- Do not commit message text, personal contact details, OTPs, financial information or message-level annotations to the public repository.

## Detector API behaviour

The local baseline API returns a **provisional model suggestion**, not a fraud verdict. It exposes uncalibrated model scores, states that review/verification is required, and explains that only message text was assessed. It cannot inspect a link destination, sender history, Android app state, device location or bank records.

The current local model is a research baseline. Do not use its output alone to freeze accounts, block transactions, accuse a person or make a consequential decision.
