"""Evaluate ScamShield on one fully source-held-out subset.

This stress test holds every candidate row tagged only as Smishing_Dataset
outside training. Cross-source duplicate groups that include Smishing_Dataset
are excluded from this experiment entirely, preventing exact text copied from
the held-out source from entering training through another source tag.

This is still an evaluation inside the same aggregated Hugging Face corpus.
It is not an independent external benchmark, verified ground truth or
real-world fraud evaluation.

Run from repository root:
    python data/train_scamshield_source_holdout.py
"""

import argparse
import json
import platform
from collections import Counter
from pathlib import Path

import joblib
import sklearn
from sklearn.model_selection import train_test_split

from split_scamshield_candidate import (
    DEFAULT_INPUT,
    build_stratification_keys,
    load_candidate_rows,
)
from train_scamshield_baseline import (
    LABEL_ORDER,
    VECTORIZER_CONFIG,
    CLASSIFIER_CONFIG,
    build_pipeline,
    calculate_metrics,
    count_labels,
    group_metrics,
    validate_splits,
)


DATA_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_ARTIFACT_DIRECTORY = DATA_DIRECTORY / "private" / "model_artifacts"
DEFAULT_HELDOUT_SOURCE = "Smishing_Dataset"


def partition_source_holdout(
    rows,
    heldout_source=DEFAULT_HELDOUT_SOURCE,
    seed=42,
    validation_fraction=0.15,
):
    """Return train, validation and test with heldout_source absent from train."""
    heldout_source = str(heldout_source).strip()
    if not heldout_source:
        raise ValueError("heldout_source cannot be blank.")
    if not 0.05 <= validation_fraction <= 0.40:
        raise ValueError("validation_fraction must be between 0.05 and 0.40.")

    test_rows = []
    development_rows = []
    overlap_excluded = []

    for row in rows:
        sources = set(row["_sources"])
        if heldout_source in sources and len(sources) == 1:
            test_rows.append(row)
        elif heldout_source in sources:
            # Do not let a held-out source's duplicate enter training under
            # another source name.
            overlap_excluded.append(row)
        else:
            development_rows.append(row)

    if not test_rows:
        raise ValueError(
            f"No single-source rows found for held-out source {heldout_source!r}."
        )
    if not development_rows:
        raise ValueError("No development rows remain after source holdout.")

    test_labels = {row["label"] for row in test_rows}
    development_labels = {row["label"] for row in development_rows}
    if test_labels != set(LABEL_ORDER):
        raise ValueError(
            "Held-out source must contain all three classes. Found: "
            + ", ".join(sorted(test_labels))
        )
    if development_labels != set(LABEL_ORDER):
        raise ValueError(
            "Remaining development sources must contain all three classes. Found: "
            + ", ".join(sorted(development_labels))
        )

    stratification_keys, raw_strata_counts = build_stratification_keys(
        development_rows
    )
    indices = list(range(len(development_rows)))
    try:
        train_indices, validation_indices = train_test_split(
            indices,
            test_size=validation_fraction,
            random_state=seed,
            stratify=stratification_keys,
        )
    except ValueError as error:
        raise ValueError(
            "Could not make a stratified train/validation partition from the "
            f"non-held-out sources: {error}"
        ) from error

    splits = {
        "train": [development_rows[index] for index in train_indices],
        "validation": [
            development_rows[index] for index in validation_indices
        ],
        "test": test_rows,
    }

    # Source-disjointness plus exact masked-text separation are postconditions.
    for row in splits["train"] + splits["validation"]:
        if heldout_source in row["_sources"]:
            raise AssertionError("Held-out source leaked into development data.")
    for row in splits["test"]:
        if row["_sources"] != [heldout_source]:
            raise AssertionError("Test contains a non-single-source row.")

    validate_splits(splits)
    return splits, {
        "heldout_source": heldout_source,
        "source_holdout_test_rows": len(test_rows),
        "development_rows_before_train_validation_split": len(development_rows),
        "cross_source_rows_excluded": len(overlap_excluded),
        "train_rows": len(splits["train"]),
        "validation_rows": len(splits["validation"]),
        "raw_language_class_counts_in_development": {
            f"{label}::{language}": count
            for (label, language), count in sorted(raw_strata_counts.items())
        },
    }


def run_experiment(
    input_path=DEFAULT_INPUT,
    artifact_directory=DEFAULT_ARTIFACT_DIRECTORY,
    heldout_source=DEFAULT_HELDOUT_SOURCE,
    seed=42,
    validation_fraction=0.15,
):
    rows, _ = load_candidate_rows(input_path)
    splits, partition_summary = partition_source_holdout(
        rows,
        heldout_source=heldout_source,
        seed=seed,
        validation_fraction=validation_fraction,
    )

    model = build_pipeline()
    model.fit(
        [row["text"] for row in splits["train"]],
        [row["label"] for row in splits["train"]],
    )

    predictions = {}
    metrics = {}
    language_metrics = {}
    for split_name in ("validation", "test"):
        split_rows = splits[split_name]
        predicted = model.predict([row["text"] for row in split_rows])
        predictions[split_name] = predicted
        metrics[split_name] = calculate_metrics(
            [row["label"] for row in split_rows], predicted
        )
        language_metrics[split_name] = group_metrics(
            split_rows, predicted, "_language"
        )

    report = {
        "experiment": "scamshield_three_class_source_heldout_stress_test",
        "dataset_id": "sidzzz07/scamshield-dataset",
        "heldout_source": heldout_source,
        "source_holdout_is_within_same_aggregated_corpus": True,
        "independent_external_test": False,
        "real_world_test": False,
        "human_verified_ground_truth": False,
        "labels_are_provisional_silver": True,
        "model": "character n-gram TF-IDF + Logistic Regression",
        "model_input": "message_text_only",
        "language_metadata_usage": "evaluation_only_not_a_model_feature",
        "model_config": {
            "vectorizer": VECTORIZER_CONFIG,
            "classifier": CLASSIFIER_CONFIG,
        },
        "random_seed": seed,
        "validation_fraction_of_non_heldout_sources": validation_fraction,
        "partition_summary": partition_summary,
        "split_class_counts": {
            name: count_labels(part)
            for name, part in splits.items()
        },
        "split_language_counts": {
            name: dict(sorted(Counter(row["_language"] for row in part).items()))
            for name, part in splits.items()
        },
        "validation_metrics": metrics["validation"],
        "validation_metrics_by_language": language_metrics["validation"],
        "heldout_source_metrics": metrics["test"],
        "heldout_source_metrics_by_language": language_metrics["test"],
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "limitations": [
            "This is a source-held-out stress test within one aggregated dataset, not an independent external benchmark.",
            "The dataset's source provenance and upstream licence lineage remain unverified.",
            "All target labels are provisional taxonomy-derived silver labels, not independently human-verified ground truth.",
            "Cross-source duplicate groups containing the held-out source were excluded from this experiment.",
            "Near-duplicate templates may still occur across source datasets; only exact masked-text groups were separated.",
            "The test source is held out by its source_dataset tag; the source tag itself is publisher metadata, not independent proof of collection provenance.",
            "This experiment does not alter SOUL's live detector, the original random split or the historical Mendeley benchmark.",
        ],
    }

    artifact_directory = Path(artifact_directory)
    artifact_directory.mkdir(parents=True, exist_ok=True)
    model_path = (
        artifact_directory / "scamshield_three_class_smishing_source_holdout.joblib"
    )
    metrics_path = (
        artifact_directory / "scamshield_three_class_smishing_source_holdout.json"
    )
    joblib.dump(model, model_path, compress=3)
    report["model_artifact_saved"] = True
    report["model_artifact_path"] = str(model_path)
    report["metrics_path"] = str(metrics_path)
    metrics_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("SOUL — ScamShield source-held-out stress test")
    print("Held-out source:", heldout_source)
    print("Train rows:", len(splits["train"]), count_labels(splits["train"]))
    print("Validation rows:", len(splits["validation"]),
          count_labels(splits["validation"]))
    print("Held-out test rows:", len(splits["test"]),
          count_labels(splits["test"]))
    print("Cross-source duplicate rows excluded:",
          partition_summary["cross_source_rows_excluded"])
    print("Held-out source appears in training: no")
    print("Held-out source appears in validation: no")
    print("Exact masked-text overlap: none")
    print("Independent external / real-world test: no")

    for split_name, display_name in (
        ("validation", "VALIDATION — non-held-out sources"),
        ("test", "HELD-OUT SOURCE TEST"),
    ):
        current = metrics[split_name]
        print(f"\n{display_name}")
        print(f"  Accuracy:          {current['accuracy']:.4f}")
        print(f"  Balanced accuracy: {current['balanced_accuracy']:.4f}")
        print(f"  Macro F1:          {current['macro_f1']:.4f}")
        print("  Macro-F1 classes included:",
              current["macro_f1_classes_included"])
        print("  Per-class precision / recall / F1 / support:")
        for label in LABEL_ORDER:
            value = current["class_metrics"][label]
            print(
                f"    {label:<11} P={value['precision']:.4f} "
                f"R={value['recall']:.4f} F1={value['f1']:.4f} "
                f"support={value['support']}"
            )
        print("  Per-language:")
        for language, value in language_metrics[split_name].items():
            print(
                f"    {language:<12} macro-F1={value['metrics']['macro_f1']:.4f} "
                f"support={value['class_support']} "
                f"{'PRELIMINARY' if value['low_support'] else ''}"
            )

    print("\nPrivate artifacts:")
    print("  Model:", model_path)
    print("  Report:", metrics_path)
    print(
        "\nImportant: source-held-out within this corpus is stronger than a "
        "random mixed-source split, but is not an independent real-world test."
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_ARTIFACT_DIRECTORY
    )
    parser.add_argument("--heldout-source", default=DEFAULT_HELDOUT_SOURCE)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-fraction", type=float, default=0.15)
    args = parser.parse_args()

    try:
        run_experiment(
            input_path=args.input_csv,
            artifact_directory=args.output_dir,
            heldout_source=args.heldout_source,
            seed=args.seed,
            validation_fraction=args.validation_fraction,
        )
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"ScamShield source-held-out experiment failed: {error}") from error


if __name__ == "__main__":
    main()
