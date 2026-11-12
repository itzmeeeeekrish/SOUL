import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_multilingual_template_families import (
    UnionFind,
    build_knn_edges,
    build_report,
    summarise_similarity_graph,
)


def make_row(split, label="scam", language="hindi"):
    return {
        "split": split,
        "label": label,
        "language": language,
    }


def test_union_find_merges_and_compresses_components():
    structure = UnionFind(5)
    structure.union(0, 1)
    structure.union(1, 2)
    structure.union(3, 4)

    assert structure.find(0) == structure.find(2)
    assert structure.find(3) == structure.find(4)
    assert structure.find(0) != structure.find(3)


def test_build_knn_edges_returns_neighbours_without_self_edges():
    matrix = csr_matrix(
        np.array(
            [
                [1.0, 0.0, 0.0],
                [0.9, 0.1, 0.0],
                [0.0, 1.0, 0.0],
            ]
        )
    )

    edges = build_knn_edges(matrix, neighbour_count=1)

    assert edges
    assert all(left != right for left, right, _ in edges)
    assert all(0.0 <= similarity <= 1.0 for _, _, similarity in edges)


def test_build_knn_edges_rejects_too_few_rows_or_invalid_neighbour_count():
    with pytest.raises(ValueError, match="At least two rows"):
        build_knn_edges(csr_matrix([[1.0, 0.0]]))
    with pytest.raises(ValueError, match="at least one"):
        build_knn_edges(csr_matrix([[1.0, 0.0], [0.0, 1.0]]), 0)


def test_similarity_graph_reports_cross_partition_candidate_component():
    rows = [
        make_row("train", "scam", "hindi"),
        make_row("validation", "scam", "hindi"),
        make_row("validation", "scam", "hindi"),
        make_row("validation", "ham", "tamil"),
    ]
    edges = [
        (0, 1, 0.97),
        (1, 2, 0.96),
        (2, 3, 0.91),
    ]

    result = summarise_similarity_graph(rows, edges, 0.95)

    assert result["non_singleton_components"] == 1
    assert result["rows_in_non_singleton_components"] == 3
    assert result["components_spanning_train_validation"] == 1
    assert result["rows_in_components_spanning_train_validation"] == 3
    assert result["components_with_multiple_labels"] == 0


def test_similarity_graph_counts_mixed_labels_and_languages_at_lower_threshold():
    rows = [
        make_row("train", "scam", "hindi"),
        make_row("validation", "ham", "tamil"),
        make_row("validation", "scam", "english"),
    ]
    edges = [
        (0, 1, 0.92),
        (1, 2, 0.91),
    ]

    result = summarise_similarity_graph(rows, edges, 0.90)

    assert result["components_with_multiple_labels"] == 1
    assert result["components_with_multiple_languages"] == 1
    assert result["cross_label_knn_edges"] == 1
    assert result["cross_language_knn_edges"] == 2


def test_similarity_graph_rejects_invalid_threshold_and_edge_indices():
    rows = [make_row("train"), make_row("validation")]

    with pytest.raises(ValueError, match="between zero and one"):
        summarise_similarity_graph(rows, [], 1.1)
    with pytest.raises(ValueError, match="outside"):
        summarise_similarity_graph(rows, [(0, 2, 0.99)], 0.9)


def test_build_report_documents_validation_only_approximate_method():
    rows = [
        make_row("train"),
        make_row("validation"),
    ]
    report = build_report(rows, [(0, 1, 0.95)])

    assert report["test_partition_read"] is False
    assert report["model_trained"] is False
    assert report["model_artifact_modified"] is False
    assert report["method"]["approximate"] is True
    assert [item["threshold"] for item in report["results"]] == [0.90, 0.95, 0.98]
