"""Audit possible synthetic-template shortcuts in the multilingual baseline.

This is a validation-only diagnostic. It does not read the initial holdout test
partition, retrain the model, change thresholds, or modify the model artifact.

Run from the repository root:
    python data/audit_multilingual_baseline.py

The report contains aggregate nearest-neighbour similarity and filtered
character n-gram coefficients only; it never prints message text.
"""

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


from train_multilingual_baseline import (
    ARTIFACT_DIRECTORY,
    LABEL_ORDER,
    MODEL_PATH,
    SPLIT_DIRECTORY,
    read_split,
)


REPORT_PATH = ARTIFACT_DIRECTORY / "multilingual_validation_diagnostics.json"
SIMILARITY_THRESHOLDS = (0.80, 0.90, 0.95)
BATCH_SIZE = 128
TOP_FEATURE_LIMIT = 20


def summarise_scores(scores, labels, nearest_labels):
    """Return aggregate similarity statistics without exposing row-level data."""
    if len(scores) == 0:
        raise ValueError("Cannot summarise an empty similarity result.")
    if not (len(scores) == len(labels) == len(nearest_labels)):
        raise ValueError("Similarity arrays have inconsistent lengths.")

    score_array = np.asarray(scores, dtype=float)
    agreement = np.asarray(
        [actual == nearest for actual, nearest in zip(labels, nearest_labels)],
        dtype=bool,
    )

    result = {
        "rows": int(len(score_array)),
        "mean_max_train_similarity": round(float(score_array.mean()), 4),
        "median_max_train_similarity": round(float(np.median(score_array)), 4),
        "p90_max_train_similarity": round(float(np.quantile(score_array, 0.90)), 4),
        "p95_max_train_similarity": round(float(np.quantile(score_array, 0.95)), 4),
        "nearest_train_label_agreement": round(float(agreement.mean()), 4),
        "similarity_threshold_counts": {},
    }

    for threshold in SIMILARITY_THRESHOLDS:
        selected = score_array >= threshold
        result["similarity_threshold_counts"][str(threshold)] = {
            "rows": int(selected.sum()),
            "fraction": round(float(selected.mean()), 4),
            "nearest_label_agreement": (
                round(float(agreement[selected].mean()), 4)
                if selected.any()
                else None
            ),
        }

    return result


def calculate_nearest_train_similarity(train_rows, validation_rows, vectorizer):
    """Compare validation messages with training messages using model features."""
    if not train_rows or not validation_rows:
        raise ValueError("Train and validation rows must both be non-empty.")

    train_texts = [row["text"] for row in train_rows]
    validation_texts = [row["text"] for row in validation_rows]
    train_labels = [row["label"] for row in train_rows]

    train_matrix = vectorizer.transform(train_texts)
    validation_matrix = vectorizer.transform(validation_texts)

    if train_matrix.shape[1] == 0 or validation_matrix.shape[1] == 0:
        raise ValueError("The fitted vectorizer produced an empty feature matrix.")

    scores = []
    nearest_labels = []

    for start in range(0, validation_matrix.shape[0], BATCH_SIZE):
        stop = min(start + BATCH_SIZE, validation_matrix.shape[0])
        batch = validation_matrix[start:stop]
        similarities = cosine_similarity(batch, train_matrix, dense_output=True)
        best_indices = np.argmax(similarities, axis=1)
        best_scores = similarities[np.arange(len(best_indices)), best_indices]

        scores.extend(float(value) for value in best_scores)
        nearest_labels.extend(train_labels[int(index)] for index in best_indices)

    labels = [row["label"] for row in validation_rows]
    overall = summarise_scores(scores, labels, nearest_labels)

    by_language = {}
    language_names = sorted({row["language"] for row in validation_rows})
    for language in language_names:
        indices = [
            index
            for index, row in enumerate(validation_rows)
            if row["language"] == language
        ]
        by_language[language] = summarise_scores(
            [scores[index] for index in indices],
            [labels[index] for index in indices],
            [nearest_labels[index] for index in indices],
        )

    return {
        "overall": overall,
        "by_language": by_language,
    }


def extract_top_character_cues(pipeline, limit=TOP_FEATURE_LIMIT):
    """Show high-weight alphabetic character n-grams for each binary class."""
    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]
    feature_names = vectorizer.get_feature_names_out()
    coefficients = classifier.coef_[0]
    classes = list(classifier.classes_)

    if len(classes) != 2:
        raise ValueError("Expected a fitted binary classifier.")

    def select(indices):
        output = []
        for index in indices:
            feature = str(feature_names[int(index)])
            # Avoid printing numeric, phone-like, URL or punctuation fragments.
            if len(feature) < 3 or not feature.isalpha():
                continue
            output.append(
                {
                    "character_ngram": feature,
                    "coefficient": round(float(coefficients[int(index)]), 5),
                }
            )
            if len(output) >= limit:
                break
        return output

    positive_indices = np.argsort(coefficients)[::-1]
    negative_indices = np.argsort(coefficients)

    return {
        "positive_direction_label": classes[1],
        "negative_direction_label": classes[0],
        "toward_scam": select(positive_indices),
        "toward_ham": select(negative_indices),
        "note": (
            "These are model-weighted character fragments, not causal rules. "
            "They may expose synthetic wording shortcuts."
        ),
    }


def main():
    if not MODEL_PATH.is_file():
        raise SystemExit(
            f"Model artifact not found: {MODEL_PATH}. "
            "Run data/train_multilingual_baseline.py first."
        )

    train_path = SPLIT_DIRECTORY / "train.csv"
    validation_path = SPLIT_DIRECTORY / "validation.csv"

    try:
        train_rows = read_split(train_path)
        validation_rows = read_split(validation_path)
        model = joblib.load(MODEL_PATH)
        if list(model.named_steps["classifier"].classes_) != list(LABEL_ORDER):
            raise ValueError("The saved model labels do not match the expected binary task.")

        train_groups = {row["group_id"] for row in train_rows}
        validation_groups = {row["group_id"] for row in validation_rows}
        if train_groups & validation_groups:
            raise ValueError("A group ID overlaps between train and validation.")

        train_hashes = {row["model_text_sha256"] for row in train_rows}
        validation_hashes = {row["model_text_sha256"] for row in validation_rows}
        if train_hashes & validation_hashes:
            raise ValueError("An exact masked text hash overlaps train and validation.")

        similarity = calculate_nearest_train_similarity(
            train_rows,
            validation_rows,
            model.named_steps["tfidf"],
        )
        top_cues = extract_top_character_cues(model)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Multilingual diagnostic failed: {error}") from error

    report = {
        "experiment": "validation_only_synthetic_template_diagnostic",
        "model_artifact": MODEL_PATH.name,
        "train_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "test_partition_read": False,
        "model_retrained": False,
        "model_artifact_modified": False,
        "exact_group_overlap": False,
        "nearest_train_similarity": similarity,
        "top_character_cues": top_cues,
        "limitations": [
            "High nearest-neighbour similarity suggests template overlap but does not prove leakage.",
            "Low similarity does not prove real-world generalisation.",
            "Character n-gram coefficients are associations, not causal explanations.",
            "The source dataset is synthetic and its language tags and labels are not independently verified.",
            "This diagnostic does not create an external real-world evaluation set.",
        ],
    }

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)

    overall = similarity["overall"]
    print("SOUL — multilingual validation-only shortcut diagnostic")
    print("Training rows:", len(train_rows))
    print("Validation rows:", len(validation_rows))
    print("Test partition read: no")
    print("Model retrained: no")
    print("Exact group/hash overlap: no")
    print("\nNearest training-message similarity (validation only):")
    print("  Mean:", overall["mean_max_train_similarity"])
    print("  Median:", overall["median_max_train_similarity"])
    print("  P90:", overall["p90_max_train_similarity"])
    print("  P95:", overall["p95_max_train_similarity"])
    print("  Nearest-train label agreement:", overall["nearest_train_label_agreement"])
    print("\nSimilarity bands:")
    for threshold, values in overall["similarity_threshold_counts"].items():
        print(
            f"  >= {threshold}: {values['rows']} rows "
            f"({values['fraction']:.1%}); "
            f"nearest-label agreement={values['nearest_label_agreement']}"
        )

    print("\nPer-language median / P95 similarity:")
    for language, values in similarity["by_language"].items():
        print(
            f"  {language:<12} "
            f"median={values['median_max_train_similarity']:.4f} "
            f"p95={values['p95_max_train_similarity']:.4f} "
            f"nearest-label-agreement={values['nearest_train_label_agreement']:.4f}"
        )

    print("\nTop model character cues (filtered to alphabetic fragments):")
    print("  Toward scam:", ", ".join(
        item["character_ngram"] for item in top_cues["toward_scam"]
    ))
    print("  Toward ham: ", ", ".join(
        item["character_ngram"] for item in top_cues["toward_ham"]
    ))
    print("\nReport saved locally:", REPORT_PATH)
    print(
        "\nInterpretation: similarity and coefficient patterns are diagnostic "
        "signals, not proof of leakage or real-world generalisation."
    )


if __name__ == "__main__":
    main()
