import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from create_multilingual_family_splits import (
    assign_family_ids,
    build_similarity_edges,
    build_summary,
    count_language_labels,
    create_family_holdout,
    validate_family_holdout,
    validate_threshold,
    write_split,
)
from train_multilingual_family_baseline import validate_family_splits


def make_row(index, label="ham", language="hindi"):
    text_hash = f"{index:064x}"
    return {
        "text": f"message {index}",
        "label": label,
        "language": language,
        "split": "train",
        "group_id": f"exact_{index}",
        "model_text_sha256": text_hash,
    }


def test_validate_threshold_accepts_only_documented_values():
    validate_threshold(0.95)
    validate_threshold(0.98)

    with pytest.raises(ValueError, match="threshold must be one of"):
        validate_threshold(0.90)


def test_build_similarity_edges_returns_undirected_edges_above_threshold():
    matrix = csr_matrix(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.99, 0.01, 0.0],
                [0.0, 1.0, 0.0],
            ],
            dtype=np.float32,
        )
    )

    edges = build_similarity_edges(matrix, 0.95, neighbour_count=1)

    assert len(edges) == 1
    assert edges[0][0:2] == (0, 1)
    assert edges[0][2] >= 0.95


def test_build_similarity_edges_rejects_too_few_rows_and_invalid_k():
    with pytest.raises(ValueError, match="At least two rows"):
        build_similarity_edges(csr_matrix([[1.0, 0.0]]), 0.95)

    matrix = csr_matrix(np.eye(2))
    with pytest.raises(ValueError, match="at least one"):
        build_similarity_edges(matrix, 0.95, neighbour_count=0)


def test_assign_family_ids_merges_edges_and_reports_mixed_label_family():
    rows = [
        make_row(1, "ham", "hindi"),
        make_row(2, "scam", "hindi"),
        make_row(3, "ham", "tamil"),
    ]

    assigned, stats = assign_family_ids(
        rows,
        [(0, 1, 0.97)],
        0.95,
    )

    assert assigned[0]["family_group_id"] == assigned[1]["family_group_id"]
    assert assigned[0]["group_id"] == assigned[1]["group_id"]
    assert assigned[2]["family_group_id"] != assigned[0]["family_group_id"]
    assert assigned[0]["original_exact_group_id"] == "exact_1"
    assert stats["families"] == 2
    assert stats["non_singleton_families"] == 1
    assert stats["mixed_label_families"] == 1
    assert stats["mixed_language_families"] == 0


def test_assign_family_ids_rejects_invalid_edge_index():
    with pytest.raises(ValueError, match="outside the row range"):
        assign_family_ids(
            [make_row(1), make_row(2)],
            [(0, 2, 0.99)],
            0.95,
        )


def test_create_family_holdout_keeps_groups_together_and_both_labels():
    rows = []
    for index in range(20):
        label = "ham" if index < 10 else "scam"
        rows.append(make_row(index, label, "hindi" if index % 2 else "english"))
        rows[-1]["family_group_id"] = f"family_{index}"

    splits = create_family_holdout(rows)

    assert set(splits) == {"train", "validation"}
    assert {row["label"] for row in splits["train"]} == {"ham", "scam"}
    assert {row["label"] for row in splits["validation"]} == {"ham", "scam"}

    train_groups = {row["family_group_id"] for row in splits["train"]}
    validation_groups = {
        row["family_group_id"] for row in splits["validation"]
    }
    assert not train_groups & validation_groups


def test_create_family_holdout_rejects_too_few_rows_or_groups():
    rows = [make_row(index) for index in range(9)]
    for row in rows:
        row["family_group_id"] = row["group_id"]

    with pytest.raises(ValueError, match="At least 10 rows"):
        create_family_holdout(rows)

    rows = [make_row(index, "ham" if index % 2 else "scam") for index in range(10)]
    for row in rows:
        row["family_group_id"] = "one_family"

    with pytest.raises(ValueError, match="At least 10 distinct"):
        create_family_holdout(rows)


def test_create_family_holdout_rejects_missing_global_label():
    rows = []
    for index in range(10):
        row = make_row(index, "ham")
        row["family_group_id"] = f"family_{index}"
        rows.append(row)

    with pytest.raises(ValueError, match="must contain ham and scam"):
        create_family_holdout(rows)


def test_validate_family_holdout_rejects_family_overlap():
    row_a = make_row(1, "ham")
    row_b = make_row(2, "scam")
    row_a["family_group_id"] = "shared"
    row_b["family_group_id"] = "shared"

    with pytest.raises(ValueError, match="similarity family crosses"):
        validate_family_holdout(
            {"train": [row_a, make_row(3, "scam")],
             "validation": [row_b, make_row(4, "ham")]}
        )


def test_validate_family_holdout_rejects_exact_text_overlap():
    row_a = make_row(1, "ham")
    row_b = make_row(2, "scam")
    row_b["model_text_sha256"] = row_a["model_text_sha256"]
    row_a["family_group_id"] = "family_train"
    row_b["family_group_id"] = "family_val"

    with pytest.raises(ValueError, match="Exact model text crosses"):
        validate_family_holdout(
            {"train": [row_a, make_row(3, "scam")],
             "validation": [row_b, make_row(4, "ham")]}
        )


def test_write_split_uses_family_group_as_model_group(tmp_path):
    row = make_row(1)
    row["family_group_id"] = "family_a"
    row["original_exact_group_id"] = row["group_id"]
    row["similarity_threshold"] = "0.95"

    path = tmp_path / "train.csv"
    write_split(path, [row], "train")

    import csv
    with path.open("r", encoding="utf-8", newline="") as source:
        saved = next(csv.DictReader(source))

    assert saved["group_id"] == "family_a"
    assert saved["family_group_id"] == "family_a"
    assert saved["original_exact_group_id"] == "exact_1"
    assert saved["split"] == "train"


def test_count_language_labels_returns_both_binary_classes():
    counts = count_language_labels(
        [
            make_row(1, "ham", "hindi"),
            make_row(2, "scam", "hindi"),
            make_row(3, "scam", "tamil"),
        ]
    )

    assert counts["hindi"] == {"ham": 1, "scam": 1}
    assert counts["tamil"] == {"ham": 0, "scam": 1}


def test_build_summary_explicitly_preserves_original_test_partition():
    rows = []
    for index in range(20):
        row = make_row(index, "ham" if index < 10 else "scam")
        row["family_group_id"] = f"family_{index}"
        rows.append(row)

    splits = create_family_holdout(rows)
    summary = build_summary(0.95, {"rows": 20}, splits)

    assert summary["original_test_partition_read"] is False
    assert summary["original_test_partition_modified"] is False
    assert summary["source_partitions_read"] == ["train", "validation"]
    assert summary["split_integrity"]["similarity_families_cross_partitions"] is False


def test_trainer_validation_accepts_disjoint_family_splits():
    train = make_row(1, "ham")
    train["family_group_id"] = "train_group"
    validation = make_row(2, "scam")
    validation["family_group_id"] = "validation_group"

    # The trainer validator accepts read_split()'s group_id field.
    validate_family_splits(
        [train, make_row(3, "scam")],
        [validation, make_row(4, "ham")],
    )


def test_trainer_validation_rejects_shared_group_or_hash():
    train = make_row(1, "ham")
    validation = make_row(2, "scam")
    validation["group_id"] = train["group_id"]

    with pytest.raises(ValueError, match="similarity family crosses"):
        validate_family_splits(
            [train, make_row(3, "scam")],
            [validation, make_row(4, "ham")],
        )
