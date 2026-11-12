"""Tests for the resumable, opt-in AI annotation batch workflow."""

import csv
import json
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from ai_annotate_prepared_dataset import (
    read_prepared_rows,
    run_annotation,
    validate_model_response,
)


def test_read_prepared_rows_uses_only_id_and_text(tmp_path):
    path = tmp_path / "prepared.csv"
    path.write_text(
        "record_id,source_label,label,text\n"
        'R1,ham,legitimate,"A simple reminder"\n',
        encoding="utf-8",
    )

    rows = read_prepared_rows(path)

    assert rows == [{"record_id": "R1", "text": "A simple reminder"}]
    assert "source_label" not in rows[0]
    assert "label" not in rows[0]


def test_validate_model_response_accepts_exact_ids_and_converts_low_confidence():
    content = json.dumps(
        {
            "annotations": [
                {
                    "id": "R1",
                    "label": "scam",
                    "confidence_band": "high",
                    "rationale": "Asks for an OTP under threat.",
                },
                {
                    "id": "R2",
                    "label": "spam",
                    "confidence_band": "low",
                    "rationale": "Promotional wording but context is unclear.",
                },
            ]
        }
    )

    result = validate_model_response(content, ["R1", "R2"])

    assert result["R1"]["ai_suggested_label"] == "scam"
    assert result["R1"]["ai_annotation_status"] == "provisional"
    assert result["R2"]["ai_suggested_label"] == "needs_review"
    assert result["R2"]["ai_annotation_status"] == "needs_review"


def test_validate_model_response_rejects_missing_ids():
    content = json.dumps(
        {
            "annotations": [
                {
                    "id": "R1",
                    "label": "spam",
                    "confidence_band": "medium",
                    "rationale": "Unwanted promotion.",
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="IDs do not match"):
        validate_model_response(content, ["R1", "R2"])


def test_validate_model_response_rejects_invalid_labels():
    content = json.dumps(
        {
            "annotations": [
                {
                    "id": "R1",
                    "label": "fraudulent",
                    "confidence_band": "high",
                    "rationale": "A rationale.",
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="unsupported label"):
        validate_model_response(content, ["R1"])


def test_run_annotation_requires_explicit_external_processing_opt_in(tmp_path):
    source = tmp_path / "prepared.csv"
    source.write_text("record_id,text\nR1,Message\n", encoding="utf-8")

    with pytest.raises(ValueError, match="External processing is disabled"):
        run_annotation(
            input_path=source,
            output_path=tmp_path / "output.csv",
            manifest_path=tmp_path / "manifest.json",
            base_url="https://example.invalid/v1",
            api_key="not-a-real-key",
            model_name="test-model",
        )


def test_run_annotation_is_resumable_and_writes_a_manifest(tmp_path):
    source = tmp_path / "prepared.csv"
    source.write_text(
        "record_id,source_label,label,text\n"
        'R1,ham,legitimate,"A simple reminder"\n'
        'R2,spam,spam,"An unwanted offer"\n',
        encoding="utf-8",
    )
    output = tmp_path / "annotations.csv"
    manifest = tmp_path / "manifest.json"
    calls = []

    def fake_request(batch, base_url, api_key, model_name):
        calls.extend(row["record_id"] for row in batch)
        return {
            row["record_id"]: {
                "ai_suggested_label": "legitimate",
                "ai_annotation_status": "provisional",
                "ai_confidence_band": "medium",
                "ai_annotation_note": "Appears to be an ordinary message.",
            }
            for row in batch
        }

    first = run_annotation(
        input_path=source,
        output_path=output,
        manifest_path=manifest,
        base_url="https://example.invalid/v1",
        api_key="not-a-real-key",
        model_name="test-model",
        batch_size=1,
        max_batches=1,
        allow_external_processing=True,
        request_function=fake_request,
    )
    assert first == (1, 1)
    assert calls == ["R1"]

    second = run_annotation(
        input_path=source,
        output_path=output,
        manifest_path=manifest,
        base_url="https://example.invalid/v1",
        api_key="not-a-real-key",
        model_name="test-model",
        batch_size=1,
        allow_external_processing=True,
        request_function=fake_request,
    )
    assert second == (2, 0)
    assert calls == ["R1", "R2"]

    with output.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    assert [row["record_id"] for row in rows] == ["R1", "R2"]
    assert all(row["ai_annotator"] == "configured_llm_api" for row in rows)

    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    assert metadata["source_label_and_baseline_label_sent"] is False
    assert "api_key" not in metadata



def test_run_annotation_rejects_mismatched_batch_response_ids(tmp_path):
    source = tmp_path / "prepared.csv"
    source.write_text("record_id,text\nR1,Message\n", encoding="utf-8")

    with pytest.raises(ValueError, match="batch response IDs"):
        run_annotation(
            input_path=source,
            output_path=tmp_path / "output.csv",
            manifest_path=tmp_path / "manifest.json",
            base_url="https://example.invalid/v1",
            api_key="not-a-real-key",
            model_name="test-model",
            allow_external_processing=True,
            request_function=lambda *_args: {},
        )

def test_run_annotation_rejects_changed_dataset_on_resume(tmp_path):
    source = tmp_path / "prepared.csv"
    source.write_text("record_id,text\nR1,Message\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "dataset_sha256": "different",
                "base_url": "https://example.invalid/v1",
                "model": "test-model",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Dataset changed"):
        run_annotation(
            input_path=source,
            output_path=tmp_path / "output.csv",
            manifest_path=manifest,
            base_url="https://example.invalid/v1",
            api_key="not-a-real-key",
            model_name="test-model",
            allow_external_processing=True,
        )
