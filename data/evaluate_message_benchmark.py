"""Evaluate SOUL's current message pipeline on a fixed synthetic challenge set.

This is a regression / challenge benchmark, not a real-world accuracy estimate.
It does not train a model, read the historical test split, or modify artifacts.
Run from any directory with the project virtual environment active:

    python data/evaluate_message_benchmark.py
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIRECTORY = ROOT / "backend"
if str(BACKEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.services.message_detector import MODEL_PATH, analyze_message  # noqa: E402


BENCHMARK_PATH = ROOT / "data" / "synthetic" / "message_evaluation_v1.csv"
DEFAULT_OUTPUT_DIRECTORY = ROOT / "data" / "private" / "evaluation"

MODEL_LABELS = ("legitimate", "spam", "scam")
FINAL_LABELS = ("legitimate", "spam", "scam", "needs_review")
ANALYSIS_STATUSES = {
    "provisional_model_suggestion",
    "abstained_protective_warning_context",
    "abstained_unsupported_language",
}
INDICATOR_CODES = {
    "credential_request",
    "urgency_or_threat",
    "kyc_or_account_update",
    "url_present",
    "upi_context",
    "remote_access_request",
    "payment_request",
}
CONTEXT_CODES = {"protective_credential_warning"}
REQUIRED_COLUMNS = {
    "case_id",
    "text",
    "expected_class",
    "expected_final_label",
    "expected_analysis_status",
    "language",
    "scenario",
    "expected_indicator_codes",
    "expected_context_codes",
    "raw_model_eligible",
    "notes",
}


def _parse_json_codes(value, field_name, case_id):
    try:
        codes = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Case {case_id}: {field_name} must contain a JSON string array."
        ) from error

    if not isinstance(codes, list):
        raise ValueError(f"Case {case_id}: {field_name} must be a JSON array.")
    if any(not isinstance(code, str) or not code for code in codes):
        raise ValueError(f"Case {case_id}: {field_name} contains an invalid code.")
    if len(codes) != len(set(codes)):
        raise ValueError(f"Case {case_id}: {field_name} contains duplicate codes.")
    return sorted(codes)


def validate_benchmark_rows(rows):
    """Validate schema, label policy, status policy and stable unique IDs."""
    if not rows:
        raise ValueError("The evaluation benchmark is empty.")

    seen_ids = set()
    seen_texts = set()

    for row in rows:
        case_id = str(row.get("case_id", "")).strip()
        text = str(row.get("text", "")).strip()
        if not case_id or not text:
            raise ValueError("Every benchmark case needs a non-empty ID and text.")
        if case_id in seen_ids:
            raise ValueError(f"Duplicate benchmark case_id: {case_id}")
        seen_ids.add(case_id)

        normalised_text = " ".join(text.casefold().split())
        if normalised_text in seen_texts:
            raise ValueError(f"Duplicate normalised benchmark text in case {case_id}.")
        seen_texts.add(normalised_text)

        expected_class = str(row.get("expected_class", "")).strip()
        final_label = str(row.get("expected_final_label", "")).strip()
        status = str(row.get("expected_analysis_status", "")).strip()
        language = str(row.get("language", "")).strip().casefold()
        eligible_value = row.get("raw_model_eligible")
        eligible = (
            eligible_value is True
            or str(eligible_value).strip().casefold() in {"true", "1", "yes"}
        )

        if expected_class and expected_class not in MODEL_LABELS:
            raise ValueError(f"Case {case_id}: invalid expected_class {expected_class!r}.")
        if final_label not in FINAL_LABELS:
            raise ValueError(f"Case {case_id}: invalid expected_final_label {final_label!r}.")
        if status not in ANALYSIS_STATUSES:
            raise ValueError(f"Case {case_id}: unsupported expected_analysis_status {status!r}.")
        if language not in {"en", "hi", "hinglish", "other"}:
            raise ValueError(f"Case {case_id}: unsupported language tag {language!r}.")

        if status == "provisional_model_suggestion":
            if not eligible or expected_class not in MODEL_LABELS:
                raise ValueError(
                    f"Case {case_id}: provisional classifier cases need an expected class."
                )
            if final_label != expected_class:
                raise ValueError(
                    f"Case {case_id}: provisional final label must match expected_class."
                )
        elif status == "abstained_protective_warning_context":
            if not eligible or expected_class not in MODEL_LABELS:
                raise ValueError(
                    f"Case {case_id}: protective-warning cases must retain an expected raw class."
                )
            if final_label != "needs_review":
                raise ValueError(
                    f"Case {case_id}: protective-warning cases must expect needs_review."
                )
        else:
            if eligible or expected_class:
                raise ValueError(
                    f"Case {case_id}: unsupported-language cases must not be raw-model scored."
                )
            if final_label != "needs_review":
                raise ValueError(
                    f"Case {case_id}: unsupported-language cases must expect needs_review."
                )

        expected_indicators = _parse_json_codes(
            row.get("expected_indicator_codes", "[]"),
            "expected_indicator_codes",
            case_id,
        )
        expected_context = _parse_json_codes(
            row.get("expected_context_codes", "[]"),
            "expected_context_codes",
            case_id,
        )
        unknown_indicators = set(expected_indicators) - INDICATOR_CODES
        unknown_context = set(expected_context) - CONTEXT_CODES
        if unknown_indicators:
            raise ValueError(
                f"Case {case_id}: unknown indicator codes {sorted(unknown_indicators)}."
            )
        if unknown_context:
            raise ValueError(
                f"Case {case_id}: unknown context codes {sorted(unknown_context)}."
            )

        row["case_id"] = case_id
        row["text"] = text
        row["expected_class"] = expected_class
        row["expected_final_label"] = final_label
        row["expected_analysis_status"] = status
        row["language"] = language
        row["raw_model_eligible"] = eligible
        row["expected_indicator_codes_list"] = expected_indicators
        row["expected_context_codes_list"] = expected_context

    return rows


def load_benchmark(path=BENCHMARK_PATH):
    """Read and validate the version-controlled synthetic benchmark."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Benchmark file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Benchmark is missing required columns: "
                + ", ".join(sorted(missing))
            )
        rows = list(reader)

    return validate_benchmark_rows(rows)


def _classification_metrics(y_true, y_pred, labels, macro_labels):
    """Return class metrics and a confusion matrix with an explicit label order."""
    if not y_true:
        return {
            "support": 0,
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
            "per_class": {},
            "confusion_matrix": [],
        }

    report = classification_report(
        y_true,
        y_pred,
        labels=list(labels),
        output_dict=True,
        zero_division=0,
    )
    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=list(labels),
    ).tolist()

    per_class = {}
    for index, label in enumerate(labels):
        values = report.get(label, {})
        true_positive = matrix[index][index]
        false_positive = sum(
            matrix[row_index][index]
            for row_index in range(len(labels))
            if row_index != index
        )
        false_negative = sum(matrix[index]) - true_positive
        true_negative = len(y_true) - true_positive - false_positive - false_negative
        false_positive_rate = (
            false_positive / (false_positive + true_negative)
            if false_positive + true_negative
            else 0.0
        )
        per_class[label] = {
            "support": int(values.get("support", 0)),
            "precision": float(values.get("precision", 0.0)),
            "recall": float(values.get("recall", 0.0)),
            "f1": float(values.get("f1-score", 0.0)),
            "false_positive": int(false_positive),
            "false_negative": int(false_negative),
            "false_positive_rate": float(false_positive_rate),
        }

    selected_f1 = [per_class[label]["f1"] for label in macro_labels]
    return {
        "support": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(sum(selected_f1) / len(selected_f1)) if selected_f1 else 0.0,
        "per_class": per_class,
        "confusion_matrix_labels": list(labels),
        "confusion_matrix": matrix,
    }


def _micro_multilabel_counts(expected_sets, actual_sets, codes):
    counts = {}
    total_tp = total_fp = total_fn = 0
    for code in sorted(codes):
        tp = sum(code in expected and code in actual for expected, actual in zip(expected_sets, actual_sets))
        fp = sum(code not in expected and code in actual for expected, actual in zip(expected_sets, actual_sets))
        fn = sum(code in expected and code not in actual for expected, actual in zip(expected_sets, actual_sets))
        total_tp += tp
        total_fp += fp
        total_fn += fn
        counts[code] = {"true_positive": tp, "false_positive": fp, "false_negative": fn}

    precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
    recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "micro": {
            "true_positive": total_tp,
            "false_positive": total_fp,
            "false_negative": total_fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "by_code": counts,
    }


def build_report(rows, results, benchmark_path=BENCHMARK_PATH):
    """Compare raw classifier, final API policy, rule signals and abstentions."""
    if len(rows) != len(results):
        raise ValueError("Benchmark rows and analysis results must have equal lengths.")

    raw_true = []
    raw_pred = []
    final_true = []
    final_pred = []
    expected_statuses = []
    actual_statuses = []
    expected_indicators = []
    actual_indicators = []
    expected_context = []
    actual_context = []
    case_reports = []
    unsupported_case_count = 0
    unsupported_model_call_count = 0
    protective_case_count = 0
    protective_abstention_count = 0
    raw_eligible_count = 0
    raw_prediction_missing_count = 0

    for row, result in zip(rows, results):
        case_id = row["case_id"]
        if not isinstance(result, dict):
            raise ValueError(f"Analyzer result for {case_id} is not a dictionary.")

        raw_candidate = result.get("model_candidate_label")
        final_candidate = result.get("candidate_label")
        actual_status = result.get("analysis_status")

        if final_candidate not in FINAL_LABELS:
            raise ValueError(
                f"Analyzer returned an invalid final label for {case_id}: {final_candidate!r}"
            )
        if actual_status not in ANALYSIS_STATUSES:
            raise ValueError(
                f"Analyzer returned an invalid analysis status for {case_id}: {actual_status!r}"
            )

        if row["raw_model_eligible"]:
            raw_eligible_count += 1
            raw_true.append(row["expected_class"])
            if raw_candidate in MODEL_LABELS:
                raw_pred.append(raw_candidate)
                raw_for_case = raw_candidate
            else:
                # An unexpected no-prediction is scored as an abstention, not silently dropped.
                raw_pred.append("needs_review")
                raw_prediction_missing_count += 1
                raw_for_case = "needs_review"
        else:
            raw_for_case = ""

        if row["expected_analysis_status"] == "abstained_unsupported_language":
            unsupported_case_count += 1
            if raw_candidate is not None or result.get("model_scores"):
                unsupported_model_call_count += 1

        if row["expected_analysis_status"] == "abstained_protective_warning_context":
            protective_case_count += 1
            if actual_status == "abstained_protective_warning_context":
                protective_abstention_count += 1

        final_true.append(row["expected_final_label"])
        final_pred.append(final_candidate)
        expected_statuses.append(row["expected_analysis_status"])
        actual_statuses.append(actual_status)

        expected_signal_set = set(row["expected_indicator_codes_list"])
        actual_signal_set = {
            item.get("code")
            for item in result.get("risk_indicators", [])
            if isinstance(item, dict) and item.get("code")
        }
        expected_context_set = set(row["expected_context_codes_list"])
        actual_context_set = {
            item.get("code")
            for item in result.get("context_flags", [])
            if isinstance(item, dict) and item.get("code")
        }

        expected_indicators.append(expected_signal_set)
        actual_indicators.append(actual_signal_set)
        expected_context.append(expected_context_set)
        actual_context.append(actual_context_set)

        case_reports.append({
            "case_id": case_id,
            "expected_class": row["expected_class"],
            "raw_model_candidate": raw_for_case,
            "expected_final_label": row["expected_final_label"],
            "final_candidate_label": final_candidate,
            "expected_analysis_status": row["expected_analysis_status"],
            "actual_analysis_status": actual_status,
            "raw_model_correct": (
                raw_for_case == row["expected_class"]
                if row["raw_model_eligible"]
                else None
            ),
            "final_result_correct": final_candidate == row["expected_final_label"],
            "expected_indicator_codes": sorted(expected_signal_set),
            "actual_indicator_codes": sorted(actual_signal_set),
            "expected_context_codes": sorted(expected_context_set),
            "actual_context_codes": sorted(actual_context_set),
        })

    raw_metrics = _classification_metrics(
        raw_true,
        raw_pred,
        labels=(*MODEL_LABELS, "needs_review"),
        macro_labels=MODEL_LABELS,
    )
    final_metrics = _classification_metrics(
        final_true,
        final_pred,
        labels=FINAL_LABELS,
        macro_labels=FINAL_LABELS,
    )

    status_matches = sum(
        expected == actual
        for expected, actual in zip(expected_statuses, actual_statuses)
    )
    expected_class_counts = dict(sorted(Counter(
        row["expected_class"]
        for row in rows
        if row["expected_class"]
    ).items()))
    final_expected_counts = dict(sorted(Counter(final_true).items()))
    final_actual_counts = dict(sorted(Counter(final_pred).items()))

    language_summary = {}
    for language in sorted({row["language"] for row in rows}):
        indices = [
            index for index, row in enumerate(rows)
            if row["language"] == language
        ]
        language_summary[language] = {
            "cases": len(indices),
            "expected_needs_review": sum(
                rows[index]["expected_final_label"] == "needs_review"
                for index in indices
            ),
            "actual_needs_review": sum(
                final_pred[index] == "needs_review"
                for index in indices
            ),
            "expected_unsupported_language_abstentions": sum(
                rows[index]["expected_analysis_status"] == "abstained_unsupported_language"
                for index in indices
            ),
            "actual_unsupported_language_abstentions": sum(
                actual_statuses[index] == "abstained_unsupported_language"
                for index in indices
            ),
        }

    benchmark_path = Path(benchmark_path)
    benchmark_hash = hashlib.sha256(benchmark_path.read_bytes()).hexdigest()

    model_hash = None
    if MODEL_PATH.is_file():
        model_hash = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()

    total = len(rows)
    return {
        "evaluation_name": "SOUL synthetic message challenge benchmark v1",
        "benchmark_version": "1.0",
        "evaluation_scope": "synthetic_constructed_regression_not_real_world_accuracy",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_file": str(benchmark_path.relative_to(ROOT))
        if benchmark_path.is_relative_to(ROOT)
        else str(benchmark_path),
        "benchmark_sha256": benchmark_hash,
        "model_name": next(
            (result.get("model") for result in results if result.get("model")),
            None,
        ),
        "model_artifact_sha256": model_hash,
        "counts": {
            "total_cases": total,
            "raw_model_eligible_cases": raw_eligible_count,
            "raw_model_expected_class_counts": expected_class_counts,
            "final_expected_label_counts": final_expected_counts,
            "final_actual_label_counts": final_actual_counts,
        },
        "raw_model_evaluation": {
            "metrics": raw_metrics,
            "expected_eligible_cases": raw_eligible_count,
            "actual_raw_predictions": raw_eligible_count - raw_prediction_missing_count,
            "unexpected_missing_predictions": raw_prediction_missing_count,
            "scope_note": (
                "Scores model_candidate_label before final safety-policy abstention. "
                "Unsupported-language cases are excluded by design."
            ),
        },
        "final_pipeline_evaluation": {
            "metrics": final_metrics,
            "scope_note": (
                "Scores candidate_label after language and protective-context policy. "
                "needs_review is a valid expected outcome for guard cases."
            ),
        },
        "analysis_status": {
            "matches": status_matches,
            "cases": total,
            "match_rate": status_matches / total if total else 0.0,
            "expected_counts": dict(sorted(Counter(expected_statuses).items())),
            "actual_counts": dict(sorted(Counter(actual_statuses).items())),
        },
        "language_guard": {
            "expected_unsupported_cases": unsupported_case_count,
            "correct_unsupported_abstentions": sum(
                expected == "abstained_unsupported_language" and actual == expected
                for expected, actual in zip(expected_statuses, actual_statuses)
            ),
            "unsupported_cases_where_model_appeared_to_run": unsupported_model_call_count,
            "by_language": language_summary,
        },
        "protective_warning_guard": {
            "expected_cases": protective_case_count,
            "correct_protective_abstentions": protective_abstention_count,
        },
        "indicator_evaluation": _micro_multilabel_counts(
            expected_indicators, actual_indicators, INDICATOR_CODES
        ),
        "context_flag_evaluation": _micro_multilabel_counts(
            expected_context, actual_context, CONTEXT_CODES
        ),
        "limitations": [
            "All cases are constructed synthetic examples, not messages collected from real users.",
            "Expected labels and signal tags are scenario-defined benchmark annotations, not independently verified ground truth.",
            "The benchmark is small and does not represent real-world message prevalence, new scam campaigns or all languages.",
            "Do not present these metrics as production accuracy or use this benchmark alone to tune a model.",
            "The evaluator does not train a model or read the frozen Mendeley test partition.",
            "Model scores remain uncalibrated and are not probabilities of fraud.",
        ],
        "_case_reports": case_reports,
    }


def run_evaluation(
    benchmark_path=BENCHMARK_PATH,
    output_directory=DEFAULT_OUTPUT_DIRECTORY,
    analyzer=None,
):
    """Run the benchmark using the live message-analysis service."""
    benchmark_path = Path(benchmark_path)
    rows = load_benchmark(benchmark_path)
    active_analyzer = analyzer or analyze_message
    results = [active_analyzer(row["text"]) for row in rows]

    report = build_report(rows, results, benchmark_path=benchmark_path)
    case_reports = report.pop("_case_reports")
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    report_path = output_directory / "message_evaluation_v1_report.json"
    cases_path = output_directory / "message_evaluation_v1_cases.csv"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    case_columns = [
        "case_id",
        "expected_class",
        "raw_model_candidate",
        "expected_final_label",
        "final_candidate_label",
        "expected_analysis_status",
        "actual_analysis_status",
        "raw_model_correct",
        "final_result_correct",
        "expected_indicator_codes",
        "actual_indicator_codes",
        "expected_context_codes",
        "actual_context_codes",
    ]
    with cases_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=case_columns)
        writer.writeheader()
        for case in case_reports:
            writer.writerow({
                **case,
                "expected_indicator_codes": json.dumps(case["expected_indicator_codes"]),
                "actual_indicator_codes": json.dumps(case["actual_indicator_codes"]),
                "expected_context_codes": json.dumps(case["expected_context_codes"]),
                "actual_context_codes": json.dumps(case["actual_context_codes"]),
            })

    return report, report_path, cases_path


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate SOUL on the fixed synthetic message challenge benchmark."
    )
    parser.add_argument("--benchmark", type=Path, default=BENCHMARK_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIRECTORY)
    args = parser.parse_args()

    try:
        report, report_path, cases_path = run_evaluation(
            benchmark_path=args.benchmark,
            output_directory=args.output_dir,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        parser.error(str(error))

    raw = report["raw_model_evaluation"]["metrics"]
    final = report["final_pipeline_evaluation"]["metrics"]
    print("SOUL synthetic message challenge benchmark")
    print(f"Cases: {report['counts']['total_cases']}")
    print(
        "Raw-model accuracy: "
        + (f"{raw['accuracy']:.4f}" if raw["accuracy"] is not None else "n/a")
    )
    print(
        "Raw-model macro-F1: "
        + (f"{raw['macro_f1']:.4f}" if raw["macro_f1"] is not None else "n/a")
    )
    print(f"Final-pipeline accuracy: {final['accuracy']:.4f}")
    print(f"Analysis-status match rate: {report['analysis_status']['match_rate']:.4f}")
    print(
        "Unsupported-language abstentions: "
        f"{report['language_guard']['correct_unsupported_abstentions']}/"
        f"{report['language_guard']['expected_unsupported_cases']}"
    )
    print(
        "Protective-warning abstentions: "
        f"{report['protective_warning_guard']['correct_protective_abstentions']}/"
        f"{report['protective_warning_guard']['expected_cases']}"
    )
    print(f"Aggregate report: {report_path}")
    print(f"Case-level results (no message text): {cases_path}")
    print("Scope: synthetic regression evidence only; not real-world accuracy.")


if __name__ == "__main__":
    main()
