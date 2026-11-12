import csv
import json
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from split_scamshield_candidate import (
    build_manifest,
    load_candidate_rows,
    make_splits,
    write_split_outputs,
)


def make_rows(repeats=20):
    rows = []
    labels = ["legitimate", "spam", "scam"]
    languages = ["english", "hindi"]
    index = 0
    for label in labels:
        for language in languages:
            for _ in range(repeats):
                index += 1
                rows.append({
                    "model_row_id": f"SS_{index:04d}",
                    "text": f"Masked sample message {index}",
                    "label": label,
                    "label_provenance": "provisional_test_fixture",
                    "masked_text_sha256": f"{index:064x}",
                    "occurrence_count": "1",
                    "source_datasets_json": json.dumps(["source_a"]),
                    "languages_json": json.dumps([language]),
                    "source_intents_json": json.dumps([label]),
                    "source_binary_labels_json": json.dumps(["1"]),
                    "publisher_splits_json": json.dumps(["train"]),
                    "source_split_groups_json": json.dumps(["source_a::bucket"]),
                    "record_ids_json": json.dumps([f"record_{index}"]),
                    "cross_source_duplicate_group": "0",
                    "cross_publisher_split_duplicate_group": "0",
                })
    return rows


def write_candidate_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_make_splits_assigns_every_group_once_and_has_no_hash_overlap():
    rows = make_rows()
    splits, _ = make_splits(rows, seed=42)

    assert sum(len(part) for part in splits.values()) == len(rows)
    assert len(splits["train"]) > len(splits["validation"])
    assert len(splits["train"]) > len(splits["test"])

    hashes = {
        name: {row["masked_text_sha256"] for row in part}
        for name, part in splits.items()
    }
    assert hashes["train"].isdisjoint(hashes["validation"])
    assert hashes["train"].isdisjoint(hashes["test"])
    assert hashes["validation"].isdisjoint(hashes["test"])


def test_make_splits_is_deterministic_for_same_seed():
    rows = make_rows()
    first, _ = make_splits(rows, seed=19)
    second, _ = make_splits(rows, seed=19)

    for name in first:
        assert [
            row["model_row_id"] for row in first[name]
        ] == [
            row["model_row_id"] for row in second[name]
        ]


def test_make_splits_changes_assignment_for_different_seed():
    rows = make_rows()
    first, _ = make_splits(rows, seed=42)
    second, _ = make_splits(rows, seed=43)

    first_train = {row["model_row_id"] for row in first["train"]}
    second_train = {row["model_row_id"] for row in second["train"]}
    assert first_train != second_train


def test_stratification_preserves_all_three_classes_in_each_split():
    rows = make_rows()
    splits, _ = make_splits(rows)

    expected = {"legitimate", "spam", "scam"}
    for part in splits.values():
        assert {row["label"] for row in part} == expected


def test_stratification_preserves_supported_language_class_slices():
    rows = make_rows()
    splits, _ = make_splits(rows)

    for part in splits.values():
        observed = {(row["label"], row["_language"]) for row in part}
        expected = {
            (label, language)
            for label in ("legitimate", "spam", "scam")
            for language in ("english", "hindi")
        }
        assert observed == expected


def test_small_language_class_slices_use_label_level_rare_bucket():
    rows = make_rows(repeats=20)
    for row in rows:
        if row["label"] == "scam" and row["languages_json"] == '["hindi"]':
            row["languages_json"] = '["assamese"]'

    _, raw_counts = make_splits(rows)
    assert raw_counts[("scam", "assamese")] == 20


def test_duplicate_masked_hashes_are_rejected(tmp_path):
    rows = make_rows()
    rows[1]["masked_text_sha256"] = rows[0]["masked_text_sha256"]
    path = tmp_path / "duplicate.csv"
    write_candidate_csv(path, rows)

    with pytest.raises(ValueError, match="duplicate masked-text hashes"):
        load_candidate_rows(path)


def test_multiple_language_tags_are_rejected(tmp_path):
    rows = make_rows()
    rows[0]["languages_json"] = '["english", "hindi"]'
    path = tmp_path / "mixed_language.csv"
    write_candidate_csv(path, rows)

    with pytest.raises(ValueError, match="conflicting language tags"):
        load_candidate_rows(path)


def test_unexpected_label_is_rejected(tmp_path):
    rows = make_rows()
    rows[0]["label"] = "needs_review"
    path = tmp_path / "review.csv"
    write_candidate_csv(path, rows)

    with pytest.raises(ValueError, match="Unexpected candidate label"):
        load_candidate_rows(path)


def test_manifest_explicitly_disclaims_source_independence_and_ground_truth():
    rows = make_rows()
    splits, raw_counts = make_splits(rows)
    manifest = build_manifest(splits, raw_counts, 42, "private.csv")

    assert manifest["publisher_split_used"] is False
    assert manifest["source_disjointness_enforced"] is False
    assert manifest["independent_external_test_created"] is False
    assert manifest["real_world_test_created"] is False
    assert manifest["human_verified_ground_truth"] is False
    assert manifest["exact_masked_text_overlap_between_splits"] is False


def test_write_split_outputs_creates_three_csvs_and_manifest(tmp_path):
    rows = make_rows()
    splits, raw_counts = make_splits(rows)
    manifest = build_manifest(splits, raw_counts, 42, "private.csv")
    fieldnames = list(rows[0])

    outputs = write_split_outputs(splits, manifest, fieldnames, tmp_path)

    for name in ("train", "validation", "test"):
        assert outputs[name].is_file()
        with outputs[name].open("r", encoding="utf-8-sig", newline="") as source:
            saved = list(csv.DictReader(source))
        assert len(saved) == len(splits[name])

    saved_manifest = json.loads(
        outputs["manifest"].read_text(encoding="utf-8")
    )
    assert saved_manifest["split_row_counts"] == {
        name: len(part) for name, part in splits.items()
    }


def test_too_small_dataset_is_rejected():
    with pytest.raises(ValueError, match="At least 30"):
        make_splits(make_rows(repeats=1))


def test_loader_rejects_missing_candidate_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Run data/prepare_scamshield_candidate.py"):
        load_candidate_rows(tmp_path / "missing.csv")


def test_loader_rejects_empty_candidate_file(tmp_path):
    rows = make_rows()
    path = tmp_path / "empty.csv"
    path.write_text(",".join(rows[0].keys()) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="contains no rows"):
        load_candidate_rows(path)
