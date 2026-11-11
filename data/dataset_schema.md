# SOUL Message Dataset Schema

**Status:** Dataset v2 schema for Milestone 2. The v2 starter CSV contains synthetic examples only.

## Purpose

Keep every SMS example in a consistent, auditable format so that SOUL can later train and evaluate a baseline text classifier.

## CSV fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `message_id` | string | Yes | Stable unique ID. Must not contain personal identifiers. |
| `text` | string | Yes | Message text. Preserve its language and spelling. |
| `label` | category | Yes | One of `legitimate`, `spam`, or `scam`. |
| `language` | category | Yes | `en`, `hi`, `hinglish`, or `other`. |
| `scenario` | string | Yes | Broad context such as `account_alert`, `delivery_update`, `kyc_phishing`, or `upi_collect`. |
| `campaign_group` | string | Yes | Identifies four related synthetic variants from one underlying template family. All variants in a group share one label and one split. Metadata only; never a model input. |
| `split` | category | Yes | Preassigned `train`, `validation`, or `test` group. Metadata only; never a model input. |
| `origin` | category | Yes | Current starter rows use `synthetic`. Future values must be documented before use. |
| `annotation_note` | string | Yes | Brief label rationale. Audit metadata only; never a model input. |

## Model input and target

For the first baseline, use only `text` as the input feature and `label` as the target.

Do not train on `annotation_note`, `scenario`, `campaign_group`, `split`, `origin` or `message_id`. These fields are audit/split metadata and would leak information or identifiers into evaluation.

## Validation rules

1. Every `message_id` must be unique.
2. Required fields cannot be blank.
3. Labels, languages and split names must use the documented values.
4. Every campaign group must contain four variants, one label and one split.
5. All rows from one `campaign_group` must remain in the same data split.
6. Remove or mask personal data before accepting any real message into a research dataset.
7. Keep source text and cleaned/model-ready text separate.
8. Never commit real OTPs, passwords, payment credentials, bank account numbers, phone numbers, Aadhaar/PAN details or private conversations.

## Dataset versions

- `data/synthetic/sms_messages.csv`: original 24-row schema smoke-test set; it predates the explicit split field.
- `data/synthetic/sms_messages_v2.csv`: 84-row synthetic set, 21 campaign groups and group-safe split assignments.

## Dataset v2 split design

Each label has seven campaign groups, with four variants per group:

| Split | Groups per label | Rows per label | Total rows | Approx. share |
|---|---:|---:|---:|---:|
| Train | 5 | 20 | 60 | 71.4% |
| Validation | 1 | 4 | 12 | 14.3% |
| Test | 1 | 4 | 12 | 14.3% |
| **Total** | **7** | **28** | **84** | **100%** |

All variants from one campaign stay together. This is a teaching/demo partition only. Validation and test sets are very small and synthetic; their model scores cannot support a real-world performance claim.

## Validate Dataset v2

From the repository root, run:

```powershell
python data/validate_dataset.py
```

The script checks required columns, blank fields, unique IDs, approved labels/languages/splits, class counts, campaign consistency, four variants per group and group isolation across splits.

## Future dataset extensions

Document the need and privacy impact before adding fields. Possible audit fields include source dataset ID, coarse collection date, reviewer and second-review result. Do not add sender phone numbers or user identity fields without a specific approved need.


## Local third-party prepared-data label provenance

The local prepared Mendeley derivative uses extra fields so the source annotation and any future SOUL human review cannot overwrite each other:

| Field | Meaning |
|---|---|
| `source_label` | Publisher's original label, normalised to lowercase: `ham`, `smishing`, `spam` |
| `label` | Provisional mapping used by the historical baseline: `legitimate`, `scam`, `spam`. Retained for compatibility with the frozen baseline and existing split. |
| `soul_label` | Empty until a human review; then `legitimate`, `spam`, `scam`, or `needs_review` |
| `review_status` | `pending`, `reviewed`, or `needs_review` |
| `annotation_note` | Short evidence-based reason for a completed review; blank while pending |

The first baseline continues to use `label`. Do not substitute `soul_label` into the existing split or model. A future reviewed-label experiment must be a separate dataset version with a new split and separate metrics.

See [label_review_protocol.md](label_review_protocol.md) for the review rules and safe workflow. Raw/prepared records remain local under Git-ignored `data/private/`.
