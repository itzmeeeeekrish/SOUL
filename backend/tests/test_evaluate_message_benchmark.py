"""Tests for the synthetic message evaluation harness."""

import csv
import json
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from evaluate_message_benchmark import (  # noqa: E402
    build_report,
    load_benchmark,
    run_evaluation,
    validate_benchmark_rows,
)


def make_case(
    case_id="T001",
    *,
    expected_class="legitimate",
    expected_final_label="legitimate",
    expected_status="provisional_model_suggestion",
    raw_eligible="true",
    indicators=None,
    contexts=None,
    text="A synthetic test message.",
):
    return {
        "case_id": case_id,
        "text": text,
        "expected_class": expected_class,
        "expected_final_label": expected_final_label,
        "expected_analysis_status": expected_status,
        "language": "en",
        "scenario": "test_scenario",
        "expected_indicator_codes": json.dumps(indicators or []),
        "expected_context_codes": json.dumps(contexts or []),
        "raw_model_eligible": raw_eligible,
        "notes": "Synthetic unit-test case.",
    }


def make_result(
    *,
    raw="legitimate",
    final="legitimate",
    status="provisional_model_suggestion",
    indicators=None,
    contexts=None,
    scores=None,
):
    return {
        "model": "fake-model-for-tests",
        "model_candidate_label": raw,
        "candidate_label": final,
        "analysis_status": status,
        "model_scores": scores if scores is not None else {
            "legitimate": 0.8,
            "scam": 0.1,
            "spam": 0.1,
        },
        "risk_indicators": [
            {"code": code}
            for code in (indicators or [])
        ],
        "context_flags": [
            {"code": code}
            for code in (contexts or [])
        ],
    }


def test_fixed_benchmark_has_balanced_raw_model_classes():
    rows = load_benchmark()

    assert len(rows) == 72
    raw_counts = {}
    for row in rows:
        if row["raw_model_eligible"]:
            raw_counts[row["expected_class"]] = (
                raw_counts.get(row["expected_class"], 0) + 1
            )

    assert raw_counts == {
        "legitimate": 22,
        "spam": 22,
        "scam": 22,
    }


def test_benchmark_has_separate_protective_and_language_guard_cases():
    rows = load_benchmark()

    protective = [
        row for row in rows
        if row["expected_analysis_status"] == "abstained_protective_warning_context"
    ]
    unsupported = [
        row for row in rows
        if row["expected_analysis_status"] == "abstained_unsupported_language"
    ]

    assert len(protective) == 6
    assert len(unsupported) == 6
    assert all(row["expected_final_label"] == "needs_review" for row in protective + unsupported)
    assert all(not row["raw_model_eligible"] for row in unsupported)


def test_validation_rejects_duplicate_case_ids():
    rows = [
        make_case("T001", text="First unique synthetic message."),
        make_case("T001", text="Second unique synthetic message."),
    ]

    with pytest.raises(ValueError, match="Duplicate benchmark case_id"):
        validate_benchmark_rows(rows)


def test_validation_rejects_unknown_indicator_code():
    rows = [
        make_case(
            indicators=["made_up_indicator"],
        )
    ]

    with pytest.raises(ValueError, match="unknown indicator codes"):
        validate_benchmark_rows(rows)


def test_raw_model_and_final_pipeline_metrics_are_separate():
    rows = [
        make_case(
            "T001",
            expected_class="legitimate",
            expected_final_label="legitimate",
        ),
        make_case(
            "T002",
            expected_class="legitimate",
            expected_final_label="needs_review",
            expected_status="abstained_protective_warning_context",
            contexts=["protective_credential_warning"],
            text="Never share your OTP.",
        ),
    ]
    validate_benchmark_rows(rows)

    results = [
        make_result(raw="scam", final="legitimate"),
        make_result(
            raw="scam",
            final="needs_review",
            status="abstained_protective_warning_context",
            contexts=["protective_credential_warning"],
        ),
    ]

    report = build_report(rows, results, benchmark_path=Path(__file__))

    raw_metrics = report["raw_model_evaluation"]["metrics"]
    final_metrics = report["final_pipeline_evaluation"]["metrics"]

    assert raw_metrics["accuracy"] == 0.0
    assert final_metrics["accuracy"] == 1.0
    assert report["protective_warning_guard"]["correct_protective_abstentions"] == 1


def test_unsupported_language_is_excluded_from_raw_model_metrics():
    rows = [
        make_case(
            "T001",
            expected_class="",
            expected_final_label="needs_review",
            expected_status="abstained_unsupported_language",
            raw_eligible="false",
            text="आपका बैंक खाता बंद हो जाएगा।",
        )
    ]
    validate_benchmark_rows(rows)
    result = make_result(
        raw=None,
        final="needs_review",
        status="abstained_unsupported_language",
        scores={},
    )

    report = build_report(rows, [result], benchmark_path=Path(__file__))

    assert report["raw_model_evaluation"]["metrics"]["support"] == 0
    assert report["final_pipeline_evaluation"]["metrics"]["support"] == 1
    assert report["language_guard"]["correct_unsupported_abstentions"] == 1
    assert report["language_guard"]["unsupported_cases_where_model_appeared_to_run"] == 0


def test_indicator_metrics_count_expected_and_unexpected_signals():
    rows = [
        make_case(
            "T001",
            expected_class="scam",
            expected_final_label="scam",
            indicators=["url_present"],
        ),
        make_case(
            "T002",
            expected_class="spam",
            expected_final_label="spam",
            text="A second synthetic marketing message.",
        ),
    ]
    validate_benchmark_rows(rows)

    results = [
        make_result(
            raw="scam",
            final="scam",
            indicators=["url_present", "urgency_or_threat"],
        ),
        make_result(
            raw="spam",
            final="spam",
            indicators=["credential_request"],
        ),
    ]
    report = build_report(rows, results, benchmark_path=Path(__file__))

    micro = report["indicator_evaluation"]["micro"]
    assert micro["true_positive"] == 1
    assert micro["false_positive"] == 2
    assert micro["false_negative"] == 0
    assert micro["precision"] == pytest.approx(1 / 3)
    assert micro["recall"] == 1.0


def test_run_evaluation_writes_aggregate_and_text_free_case_files(tmp_path):
    benchmark = DATA_DIRECTORY / "synthetic" / "message_evaluation_v1.csv"

    fake_result = make_result(
        raw=None,
        final="needs_review",
        status="abstained_unsupported_language",
        scores={},
    )
    report, report_path, cases_path = run_evaluation(
        benchmark_path=benchmark,
        output_directory=tmp_path,
        analyzer=lambda _text: fake_result,
    )

    assert report["counts"]["total_cases"] == 72
    assert report_path.is_file()
    assert cases_path.is_file()

    saved_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert "limitations" in saved_report

    with cases_path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        assert "text" not in reader.fieldnames
        case_rows = list(reader)

    assert len(case_rows) == 72
    assert "Your sign-in verification code" not in cases_path.read_text(encoding="utf-8")
