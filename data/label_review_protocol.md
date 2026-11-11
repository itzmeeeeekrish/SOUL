# SOUL Label Review Protocol

**Version:** 0.1  
**Status:** Proposed human-review workflow; no third-party records have been relabelled.

## Why this exists

The first baseline maps the Mendeley source labels to SOUL's three working categories:

| Original source label | Provisional baseline label |
|---|---|
| `ham` | `legitimate` |
| `smishing` | `scam` |
| `spam` | `spam` |

Manual review of 31 validation mistakes found 19 errors between the provisional `spam` and `scam` categories. Some source `smishing` examples resemble commercial promotions or premium-service solicitations, while some source `spam` examples resemble ordinary service messages. These observations justify a careful review; they do not prove which individual labels are correct.

## Preserve four separate pieces of information

The local prepared CSV contains these label and review fields:

| Field | Meaning | Initial value |
|---|---|---|
| `source_label` | Original category supplied by Mendeley, normalised only for case/whitespace | `ham`, `smishing`, or `spam` |
| `label` | Provisional mapping used by the historical baseline and existing split | `legitimate`, `scam`, or `spam` |
| `soul_label` | SOUL's independently reviewed label | Blank until a human review |
| `review_status` | Human-review state | `pending` |
| `annotation_note` | Short reason supporting a human decision | Blank until review |

**Compatibility rule:** The first baseline continues to use `label`. Do not replace it with `soul_label` or edit the existing split/model artefacts. The historical baseline must remain reproducible.

## SOUL annotation definitions

- **`legitimate`:** Expected or benign communication without deceptive or unsolicited promotional intent.
- **`spam`:** Unsolicited bulk/promotion/marketing or unwanted commercial solicitation without a clear deceptive attempt to steal credentials, obtain money under false pretences, or compromise an account/device.
- **`scam`:** Deceptive or manipulative communication intended to obtain money, credentials, account access, personal secrets, or another harmful action. Impersonation, fake payment/KYC demands and malicious login destinations may support this label.
- **`needs_review`:** The available message and context do not support a defensible decision. This is a review state, not a fourth model class.

A prize offer, paid service, shortened URL, urgent phrase, bank name, or unknown sender alone is not enough to establish a scam. Assess the message's claim, context and requested action. An advertisement can be spam without being fraud. A message that impersonates a trusted party or tricks the recipient into paying/revealing secrets may be a scam.

## Review-state rules

| `review_status` | `soul_label` | `annotation_note` |
|---|---|---|
| `pending` | Blank | Blank |
| `reviewed` | One of `legitimate`, `spam`, `scam` | Required; concise evidence-based reason |
| `needs_review` | `needs_review` | Required; explain what context is missing or ambiguous |

Do not infer a SOUL label from the model prediction. Keep the predicted label as a separate model-output field in any review queue. If two reviewers disagree, preserve the disagreement and use `needs_review` until adjudicated.

## Safe review sequence

1. Regenerate the local prepared derivative with the updated preparation utility.
2. Run the prepared-data validator. All new label-provenance and review-state checks should pass.
3. Review a small, prioritised queue of validation errors locally. Do not publish the SMS text or private working CSV.
4. Add SOUL labels only after applying the definitions above; leave ambiguous examples as `needs_review`.
5. Keep the first model's `label`, the existing train/validation/test split, the model artifact and the initial test metrics frozen.
6. Only after a separate reviewed dataset version is available should a new experiment use `soul_label` as the target. Create a new, campaign-aware split and report its metrics separately from the original baseline.

## Privacy and source limitations

- The prepared text uses regex-based masking, which is not guaranteed anonymisation.
- Keep raw archive, prepared records, review queues and row-level labels in Git-ignored `data/private/`.
- Never put SMS content, contact information, OTPs, bank details or other personal information in GitHub issues, commits, documentation examples or public chats.
- A human label is an annotation decision, not proof that a real message sender committed fraud.
- Source licensing and privacy approval are separate gates; this workflow does not approve redistribution of the dataset.


## Blinded review of baseline validation errors

A helper script creates a review sheet for the 31 known validation misclassifications:

```powershell
python data\\analyze_baseline_errors.py
python data\\build_validation_label_review_queue.py
```

The builder verifies the validation split hash, checks every error row against its exact validation text and label, maps the masked text back to the prepared source-label provenance, and rejects ambiguous source-label matches.

It creates two local files under `data/private/model_artifacts/`:

- `validation_label_review_blind.csv`: `review_id`, text, blank `soul_label`, `review_status=pending`, blank `annotation_note`. It deliberately excludes original source labels and model predictions.
- `validation_label_review_key.csv`: review ID, source label, provisional baseline label, model prediction, top-class score and source-occurrence count. It deliberately contains no message text.

**Review the blind file first. Do not open the key until you have completed independent labels.** Enter one of `legitimate`, `spam`, `scam`, or `needs_review` in `soul_label`; set `review_status` to `reviewed` or `needs_review`; add a concise evidence-based `annotation_note`. If uncertain, use `needs_review`.

This is an error-focused sample selected because the baseline got it wrong. It is not representative of the full dataset and must not be used to estimate class proportions or model performance. It is a targeted annotation exercise to investigate confusing examples. Keep both files private; the blind file contains message text. Do not commit, upload or share it.
