# Multilingual Synthetic Template-Family Validation

**Status:** Experimental development protocol; not a production or real-world validation result.

## Why this experiment exists

The initial 14-language synthetic binary pilot produced 99.91% validation and initial-holdout accuracy. Exact masked-text groups were separated, but a train-to-validation nearest-neighbour diagnostic found high character similarity:

- Mean nearest-training similarity: 0.9062.
- Median: 0.9512.
- 50.8% of validation rows had a nearest training row at similarity >= 0.95.
- Nearest-training label agreement: 99.91%.

Removing six explicit privacy placeholders did not change validation metrics. Similar synthetic wording/template families therefore remain a plausible shortcut, but are not proven to be the sole explanation.

## Safe development-pool rule

The create_multilingual_family_splits.py utility reads only the already-prepared train.csv and validation.csv files. It does **not** open the original initial-holdout test.csv.

This is intentional. The existing original test result and artifact remain unchanged. The old validation rows have appeared in prior diagnostics, so the family-separated result is a new development diagnostic, not a fresh independent final test.

## Family construction

The split utility:

1. Loads the existing multilingual baseline pipeline. Its character TF-IDF vectorizer was fitted on the original training partition only.
2. Transforms the pooled original train + validation message text; it does not fit a new vocabulary or use labels for similarity.
3. Finds up to five nearest non-self neighbours per row by cosine similarity.
4. Adds an undirected edge when similarity meets the requested threshold.
5. Uses connected components as approximate candidate template families.
6. Uses StratifiedGroupKFold to allocate whole families to approximately 90% train / 10% validation. The stratification target is the binary label; language distributions are reported rather than forced.
7. Verifies no family ID or exact model-text hash crosses the new partitions.

Run separately for two exploratory thresholds:

    python data/create_multilingual_family_splits.py --threshold 0.95
    python data/create_multilingual_family_splits.py --threshold 0.98

Outputs are stored under:

- data/private/multilingual_candidates/family_splits/threshold_095/
- data/private/multilingual_candidates/family_splits/threshold_098/

The graph is approximate because it uses top-K neighbours. Connected components use single-link chaining: A can be connected to C through B even when A and C are not directly similar. Similarity families are not verified campaigns or authorship groups. A connected component can also include mixed labels; it is kept intact rather than silently dropping a difficult example.

## Family-separated baseline

After each split has been created, run:

    python data/train_multilingual_family_baseline.py --threshold 0.95
    python data/train_multilingual_family_baseline.py --threshold 0.98

The trainer uses the fixed character n-gram TF-IDF + Logistic Regression recipe. It reads only the family split's train and validation files, reports aggregate and per-language validation metrics, and saves aggregate JSON only. It does not save another model artifact, open a test partition, modify the original multilingual model, or change the three-class SOUL API detector.

The two threshold results can be compared as development diagnostics only. Do not choose a threshold based on test metrics; no test metrics are calculated here.

## Interpretation rules

- A lower family-separated validation score than 99.91% would support the hypothesis that the original split benefited from similar template families across partitions. It would not prove the model is useless.
- A high score would not establish real-world performance; the dataset is still synthetic and generated patterns may remain consistent across family groups.
- Small language/class support must be labelled preliminary. Report per-language ham/scam support beside every subgroup metric.
- Do not describe ham as independently verified legitimate communication.
- Do not map this binary ham/scam model into the existing three-class legitimate/spam/scam detector.
- Do not remove the current Hindi/Hinglish language guard based on this experiment.

## What would establish stronger evidence

The next major evaluation step is a source-held-out corpus with documented collection/generation provenance and compatible scam/ham semantics, preferably real, consented or responsibly redacted Indian messages. Source and licence terms must be checked first. AI-generated labels remain provisional silver labels, not independent ground truth.

Regex masking returning zero residual candidates is not proof that all personal information has been removed. Keep row-level artifacts local under Git-ignored data/private/.
