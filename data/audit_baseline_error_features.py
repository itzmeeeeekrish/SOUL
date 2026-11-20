"""Validation-only feature diagnostics for SOUL's frozen text classifier.

Run from the repository root:
    python data/audit_baseline_error_features.py

Reads only the saved validation split and the locally generated model artifact.
It does not train, tune, read test.csv, or export message text. The JSON report
contains aggregate metrics and model feature terms only; keep it Git-ignored
and review feature terms before sharing because vocabulary terms can still
contain sensitive fragments.
"""

import json
from collections import defaultdict
from pathlib import Path

import joblib

from train_text_baseline import (
    ARTIFACT_DIRECTORY,
    LABEL_ORDER,
    METRICS_PATH,
    MODEL_PATH,
    SPLIT_DIRECTORY,
    read_split,
    sha256_file,
)

REPORT_PATH = ARTIFACT_DIRECTORY / "validation_feature_error_report.json"
TOP_FEATURES_PER_MESSAGE = 5
TOP_FEATURES_PER_PAIR = 10


def _average(values):
    return round(sum(values) / len(values), 6) if values else None


def build_feature_error_report(rows, pipeline):
    """Summarise validation mistakes, vocabulary coverage and contrastive terms.

    No message text, row ID, URL or sender field is copied to the report.
    A contrastive term is a feature whose fitted logit contribution favoured
    the predicted class over the actual class for a particular error.
    """
    if not rows:
        raise ValueError("Validation rows must not be empty.")

    named_steps = getattr(pipeline, "named_steps", None)
    if not isinstance(named_steps, dict) or not {"tfidf", "classifier"} <= set(named_steps):
        raise ValueError("Pipeline must contain named 'tfidf' and 'classifier' steps.")

    vectorizer = named_steps["tfidf"]
    classifier = named_steps["classifier"]
    classes = [str(label) for label in getattr(pipeline, "classes_", ())]
    if set(classes) != set(LABEL_ORDER) or len(classes) != len(LABEL_ORDER):
        raise ValueError("Pipeline has an unexpected label schema.")

    coefficients = getattr(classifier, "coef_", None)
    if coefficients is None or len(coefficients) != len(classes):
        raise ValueError("Classifier coefficients do not match its class labels.")

    texts = [str(row.get("text") or "") for row in rows]
    actual_labels = [str(row.get("label") or "") for row in rows]
    if any(not text.strip() for text in texts):
        raise ValueError("Validation rows contain blank text.")
    if any(label not in LABEL_ORDER for label in actual_labels):
        raise ValueError("Validation rows contain an unsupported label.")

    matrix = vectorizer.transform(texts).tocsr()
    predictions = [str(value) for value in pipeline.predict(texts)]
    probabilities = pipeline.predict_proba(texts)
    if len(predictions) != len(rows) or len(probabilities) != len(rows):
        raise ValueError("Model outputs do not match the validation row count.")

    analyzer = vectorizer.build_analyzer()
    vocabulary = vectorizer.vocabulary_
    feature_names = vectorizer.get_feature_names_out()
    class_index = {label: index for index, label in enumerate(classes)}

    correct_coverages = []
    error_coverages = []
    correct_margins = []
    error_margins = []
    by_actual = {
        label: {"support": 0, "errors": 0, "coverage": [], "top_scores": []}
        for label in LABEL_ORDER
    }
    pairs = {}

    for row_index, (text, actual, predicted, scores) in enumerate(
        zip(texts, actual_labels, predictions, probabilities)
    ):
        if predicted not in LABEL_ORDER or len(scores) != len(classes):
            raise ValueError("Model returned an unexpected label or score shape.")

        tokens = analyzer(text)
        coverage = (
            sum(1 for token in tokens if token in vocabulary) / len(tokens)
            if tokens
            else None
        )
        ranked_scores = sorted((float(value) for value in scores), reverse=True)
        margin = ranked_scores[0] - ranked_scores[1]
        top_score = ranked_scores[0]

        stats = by_actual[actual]
        stats["support"] += 1
        stats["top_scores"].append(top_score)
        if coverage is not None:
            stats["coverage"].append(coverage)

        if predicted == actual:
            correct_margins.append(margin)
            if coverage is not None:
                correct_coverages.append(coverage)
            continue

        error_margins.append(margin)
        if coverage is not None:
            error_coverages.append(coverage)
        stats["errors"] += 1

        pair_key = (actual, predicted)
        pair = pairs.setdefault(
            pair_key,
            {
                "actual": actual,
                "predicted": predicted,
                "count": 0,
                "coverages": [],
                "margins": [],
                "top_scores": [],
                "features": {},
            },
        )
        pair["count"] += 1
        if coverage is not None:
            pair["coverages"].append(coverage)
        pair["margins"].append(margin)
        pair["top_scores"].append(top_score)

        actual_index = class_index[actual]
        predicted_index = class_index[predicted]
        contrast = coefficients[predicted_index] - coefficients[actual_index]

        start = matrix.indptr[row_index]
        end = matrix.indptr[row_index + 1]
        active_indices = matrix.indices[start:end]
        active_values = matrix.data[start:end]
        contributions = [
            (int(feature_index), float(value * contrast[feature_index]))
            for feature_index, value in zip(active_indices, active_values)
            if value * contrast[feature_index] > 0
        ]
        contributions.sort(key=lambda item: item[1], reverse=True)

        for feature_index, contribution in contributions[:TOP_FEATURES_PER_MESSAGE]:
            feature = str(feature_names[feature_index])
            aggregate = pair["features"].setdefault(
                feature, {"count": 0, "contribution_sum": 0.0}
            )
            aggregate["count"] += 1
            aggregate["contribution_sum"] += contribution

    error_pairs = []
    for pair_key in sorted(
        pairs,
        key=lambda key: (-pairs[key]["count"], LABEL_ORDER.index(key[0]), LABEL_ORDER.index(key[1])),
    ):
        pair = pairs[pair_key]
        ranked_features = sorted(
            pair["features"].items(),
            key=lambda item: (-item[1]["count"], -item[1]["contribution_sum"], item[0]),
        )[:TOP_FEATURES_PER_PAIR]
        error_pairs.append(
            {
                "actual": pair["actual"],
                "predicted": pair["predicted"],
                "count": pair["count"],
                "mean_vocabulary_coverage": _average(pair["coverages"]),
                "mean_top_score_margin": _average(pair["margins"]),
                "mean_top_model_score": _average(pair["top_scores"]),
                "top_contrastive_features": [
                    {
                        "feature": feature,
                        "error_count": details["count"],
                        "mean_positive_logit_contribution": round(
                            details["contribution_sum"] / details["count"], 6
                        ),
                    }
                    for feature, details in ranked_features
                ],
            }
        )

    actual_summary = {}
    for label, stats in by_actual.items():
        actual_summary[label] = {
            "support": stats["support"],
            "errors": stats["errors"],
            "mean_vocabulary_coverage": _average(stats["coverage"]),
            "mean_top_model_score": _average(stats["top_scores"]),
        }

    total_errors = len(error_margins)
    return {
        "schema_version": 1,
        "split": "validation_only",
        "total_rows": len(rows),
        "correct_rows": len(rows) - total_errors,
        "misclassified_rows": total_errors,
        "mean_vocabulary_coverage_correct": _average(correct_coverages),
        "mean_vocabulary_coverage_errors": _average(error_coverages),
        "mean_top_score_margin_correct": _average(correct_margins),
        "mean_top_score_margin_errors": _average(error_margins),
        "by_actual_label": actual_summary,
        "error_pairs": error_pairs,
        "privacy": {
            "message_text_exported": False,
            "row_ids_exported": False,
            "raw_urls_or_sender_fields_exported": False,
            "feature_terms_present": True,
            "keep_report_local": True,
        },
        "scope": {
            "validation_split_read": True,
            "test_split_read": False,
            "model_retrained": False,
            "thresholds_or_parameters_tuned": False,
        },
        "interpretation": (
            "Vocabulary coverage is the share of vectorizer tokens present in "
            "the fitted vocabulary, not language confidence. Contrastive terms "
            "show fitted TF-IDF/logistic-regression features favouring the "
            "predicted class over the actual class for observed validation errors; "
            "they are diagnostic clues, not causal explanations. Model scores "
            "and margins are uncalibrated."
        ),
    }


def main():
    validation_path = SPLIT_DIRECTORY / "validation.csv"
    if not MODEL_PATH.is_file() or not METRICS_PATH.is_file():
        raise SystemExit(
            "Baseline model/metrics not found. Run data/train_text_baseline.py "
            "from the repository root first."
        )

    try:
        rows = read_split(validation_path)
        with METRICS_PATH.open("r", encoding="utf-8") as source:
            metadata = json.load(source)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Validation diagnostic input error: {error}") from error

    expected_hash = metadata.get("split_sha256", {}).get("validation")
    if not expected_hash or expected_hash != sha256_file(validation_path):
        raise SystemExit(
            "validation.csv does not match the fingerprint saved with the baseline. "
            "No diagnostic was run."
        )

    # Only load the locally generated model artifact from this trusted project.
    pipeline = joblib.load(MODEL_PATH)
    report = build_feature_error_report(rows, pipeline)

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("SOUL — validation-only classifier feature diagnostic")
    print("Validation rows:", report["total_rows"])
    print("Correct:", report["correct_rows"])
    print("Misclassified:", report["misclassified_rows"])
    print("Mean vocabulary coverage (correct):", report["mean_vocabulary_coverage_correct"])
    print("Mean vocabulary coverage (errors):", report["mean_vocabulary_coverage_errors"])
    print("\nMisclassification pairs and leading contrastive features:")
    for pair in report["error_pairs"]:
        print(
            f"  {pair['actual']} -> {pair['predicted']}: {pair['count']} "
            f"(mean coverage={pair['mean_vocabulary_coverage']}, "
            f"mean margin={pair['mean_top_score_margin']})"
        )
        for feature in pair["top_contrastive_features"][:5]:
            print(
                f"    {feature['feature']}: in {feature['error_count']} errors"
            )

    print("\nLocal report:", REPORT_PATH)
    print("Privacy: no message text or row IDs are exported; feature terms remain local.")
    print("Scope: validation only; no retraining, tuning or test-split access.")


if __name__ == "__main__":
    main()
