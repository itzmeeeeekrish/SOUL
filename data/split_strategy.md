# SOUL Dataset v2 Split Strategy

**Date:** 10 November 2026

## Why group-based splitting?

A random row-level split can place near-identical variants of the same campaign in both training and test data. The model may appear to generalise while it has effectively seen the same template already.

Dataset v2 therefore assigns every `campaign_group` to exactly one split. The four message variants from a group always remain together.

## Fixed split assignment

There are 7 groups for each label:

- 5 groups per label are assigned to `train`.
- 1 group per label is assigned to `validation`.
- 1 group per label is assigned to `test`.

Each group contains 4 rows. This creates 60 training rows (71.4%), 12 validation rows (14.3%) and 12 test rows (14.3%).

The explicit `split` field is metadata only. The model must receive `text` and predict `label`; it must not receive campaign ID, split, scenario or annotation notes.

## Limits

This is a small synthetic demonstration. Each validation and test partition contains only 4 examples per class and one campaign family per class. A single campaign can dominate the score. Results will be useful only to check that the code runs and the split is respected—not to claim real-world performance.

For a meaningful evaluation, SOUL needs a larger, independently sourced, licence-checked, manually reviewed dataset with multiple unrelated campaigns and a source/campaign-aware holdout.


## Mendeley prepared derivative — planned split (11 November 2026)

The first local preparation produced 5,797 unique exact-text records after quarantining 68 rows with conflicting source labels. The prepared-data validator found 5,722 unique normalised masked texts, 37 repeated masked-text groups and one repeated masked-text group with multiple labels.

The first real-data split will use `data/create_mendeley_splits.py` with a fixed random seed (42):

1. Read only the local prepared CSV in `data/private/`.
2. Group by normalised final masked text (case-folding and collapsing whitespace).
3. Collapse same-label groups to one model row and sum source-occurrence counts for audit.
4. Quarantine any masked-text group whose same final text has multiple labels.
5. Stratify the remaining unique text groups independently within each class into 70% train, 15% validation and 15% test.
6. Verify that no normalised text or split group appears in more than one partition.

Outputs will be local under `data/private/mendeley_splits/`. The model must use only `text` as X and `label` as y. IDs, split group IDs, source occurrence counts and split names are audit metadata only. This first split is text-only; original and recalculated URL/EMAIL/PHONE flags are deliberately excluded.

### Limitations of this split

- This protects against exact final masked-text leakage only.
- It does not identify near-duplicate campaign families or guarantee campaign-independent evaluation.
- Masking can merge different source messages. Same-label collisions are collapsed to one input; cross-label collisions are quarantined.
- The prepared data is class-imbalanced. Split each class separately and report per-class precision/recall/F1, macro-F1 and confusion matrix. A majority-class accuracy baseline is not meaningful evidence of scam detection.
- This is an exploratory development split. Strong performance claims require independently sourced and labelled campaign-level holdouts, ideally including Indian-language messages and out-of-distribution testing.
