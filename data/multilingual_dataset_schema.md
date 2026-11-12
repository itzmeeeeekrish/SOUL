# SOUL Multilingual Message Data Schema

**Status:** Proposed schema for new language-specific research datasets. It does not modify the historical Mendeley schema or baseline CSVs.

## Required fields

| Field | Meaning |
|---|---|
| record_id | Stable generated local identifier; must not contain personal information |
| text | Privacy-reviewed message text in its original script/language |
| source_dataset | Dataset/source identifier |
| source_record_id | Original source row identifier, if available and permitted |
| source_label | Original publisher label, unchanged |
| label_task | Meaning of the source target, e.g. scam_vs_ham or spam_vs_ham |
| target_label | Label exactly as defined by that source, not silently remapped |
| language | Source-provided language tag, if available |
| script | Unicode/script category; keep separate from language |
| language_provenance | publisher, automatic, or AI_suggested |
| source_type | real_public, synthetic, or mixed |
| generator | Model/provider when content is generated; blank for non-generated rows |
| group_id | Campaign/template/source group used to prevent leakage, when available |
| split | SOUL-created train/validation/test assignment; keep source split separately |
| licence | Applicable source licence/terms reference |
| privacy_status | not_audited, pattern_audited, or approved_for_local_research |
| annotation_provenance | publisher, AI/provider/model, or other documented method |

## Optional fields

- source_split: the partition supplied by the publisher.
- scenario: known scam/communication scenario.
- scam_type: source-provided fine-grained type.
- ai_suggested_label: SOUL AI silver label, distinct from source_label and target_label.
- ai_annotation_note: brief rationale.
- ai_model, ai_method, ai_created_at: AI provenance.
- exact_text_hash: generated hash used for duplicate grouping without exposing text in reports.

## Rules

1. Do not overwrite source_label or source text.
2. Do not treat ham/spam as equivalent to legitimate/scam without reviewing the target definition.
3. Do not mix scam_vs_ham and spam_vs_ham tasks as if their positive class were the same.
4. Keep real_public and synthetic rows separately identifiable.
5. Keep generator/provider per row when known; apply provider-specific restrictions before use.
6. Remove or quarantine privacy candidates before model development; pattern masking is not proof of anonymity.
7. Split by source/campaign/template group, not by random row alone.
8. Never allow a single group or near-duplicate family to cross train, validation and test.
9. Never use synthetic-only evaluation to make real-world performance claims.
10. Preserve the original baseline's 3-class files and test results unchanged.

## SOUL's existing classes

- legitimate — benign/expected communication.
- spam — unwanted promotion without clear deceptive intent.
- scam — deceptive communication aiming at money, secrets, account access or another harmful action.
- needs_review — abstention, not an ordinary training class.

A source with only binary classes must remain a separate task until its labels can be mapped with evidence.


## Candidate 8 local derivative fields

The first local candidate derivative additionally stores:
- source_splits: publisher partitions represented by collapsed source occurrences.
- source_occurrences: number of identical masked text/language/label occurrences collapsed into this prepared row.
- original_content_sha256: hash of normalised source text, used only for local duplicate analysis.
- model_text_sha256: hash of final masked text used for group isolation.
- group_id: stable local grouping key derived from model_text_sha256.
- has_*_candidate: presence flags computed from source text before masking.
- has_residual_candidate_after_mask: whether known regex candidates remain after masking.
- split: SOUL-created group-safe partition.

The prepared and split files remain Git-ignored under data/private/. Quarantine groups with conflicting labels after masking are excluded from all three partitions.
