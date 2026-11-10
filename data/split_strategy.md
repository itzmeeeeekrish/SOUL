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
