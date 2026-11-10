# SOUL Message Dataset Schema

**Status:** Initial schema for Milestone 2. The starter CSV contains synthetic examples only.

## Purpose

Keep every SMS example in a consistent, auditable format so that SOUL can later train and evaluate a baseline text classifier.

## CSV fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `message_id` | string | Yes | Stable unique ID. Must not contain a phone number, account number or other personal identifier. |
| `text` | string | Yes | Message text as received/written. Preserve its language and spelling; do not manually remove words that may be useful signals. |
| `label` | category | Yes | One of `legitimate`, `spam`, or `scam`, assigned using the annotation guide. |
| `language` | category | Yes | `en` (English), `hi` (Hindi), `hinglish` (Hindi-English code-mixed), or `other`. |
| `scenario` | string | Yes | Broad context such as `account_alert`, `delivery`, `promotion`, `kyc`, or `upi`. Use a consistent snake_case value. |
| `campaign_group` | string | Yes | Groups duplicate or near-duplicate/template-related messages. All variants from the same campaign/template family must share one value. Used for leakage-resistant splitting, not as a model feature. |
| `origin` | category | Yes | Where the row came from. Current starter rows use `synthetic`. Future values must be documented before use. |
| `annotation_note` | string | Yes | Brief human-readable reason for the assigned label. Audit metadata only; never use it as model input. |

## Model input and target

For the first baseline:

- **Input feature:** `text` only.
- **Target:** `label`.
- **Audit/split metadata:** `message_id`, `language`, `scenario`, `campaign_group`, `origin`, and `annotation_note`.

Do not accidentally train on `annotation_note`, `scenario`, or other metadata: those fields can leak the answer into the model and make evaluation misleading.

## Data validation rules

1. Every `message_id` must be unique.
2. Required fields cannot be blank.
3. `label` must be one of the three approved labels.
4. `language` and `origin` must use documented values.
5. Rows from the same `campaign_group` must stay in the same train, validation or test split.
6. Remove or mask personal data before a row is accepted into a research dataset.
7. Keep original text and any cleaned/model-ready text in separate fields or derived files. Never silently overwrite the source text.
8. Do not put real OTPs, passwords, payment credentials, bank account numbers, phone numbers, Aadhaar/PAN details or private conversations in the repository.

## Current starter dataset

File: `data/synthetic/sms_messages.csv`

It contains 24 hand-authored synthetic examples: 8 legitimate, 8 spam and 8 scam. This balanced sample is only for checking the schema and future pipeline code. It is far too small and artificial to establish real-world model accuracy.

## Future dataset extensions

Before adding a new field, document why it is needed and whether it is safe to retain. Potential additions include source dataset ID, collection date at a coarse granularity, annotation reviewer, second-review result, and URL-presence metadata. Do not add sender phone numbers or user identity fields unless a specific, approved research need exists.
