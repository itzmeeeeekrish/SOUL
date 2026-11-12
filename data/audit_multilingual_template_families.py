"""Approximate template-family audit across train and validation only.

This audit uses a sparse character-TF-IDF k-nearest-neighbour graph to find
candidate near-duplicate/template clusters. It does not read the initial
holdout test partition, train a classifier, or change model artifacts.

Run from repository root:
    python data/audit_multilingual_template_families.py

The graph is approximate because only each row's closest K neighbours are
considered. Similarity thresholds are diagnostic heuristics, not ground truth.
Only aggregate statistics are printed/saved; message text is never output.
"""

import json
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.neighbors import NearestNeighbors

from train_multilingual_baseline import (
    ARTIFACT_DIRECTORY,
    MODEL_PATH,
    SPLIT_DIRECTORY,
    read_split,
)


REPORT_PATH = ARTIFACT_DIRECTORY / "multilingual_template_family_audit.json"
SIMILARITY_THRESHOLDS = (0.90, 0.95, 0.98)
NEIGHBOUR_COUNT = 5


class UnionFind:
    """Small disjoint-set helper for similarity-connected components."""

    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item):
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left, right):
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1


def build_knn_edges(matrix, neighbour_count=NEIGHBOUR_COUNT):
    """Return directed top-K neighbour edges as (left, right, cosine similarity)."""
    row_count = matrix.shape[0]
    if row_count < 2:
        raise ValueError("At least two rows are required for a neighbour graph.")
    if neighbour_count < 1:
        raise ValueError("neighbour_count must be at least one.")

    requested = min(neighbour_count + 1, row_count)
    model = NearestNeighbors(
        n_neighbors=requested,
        metric="cosine",
        algorithm="brute",
        n_jobs=1,
    )
    model.fit(matrix)
    distances, indices = model.kneighbors(matrix)

    edges = []
    for row_index in range(row_count):
        for distance, neighbour_index in zip(
            distances[row_index],
            indices[row_index],
        ):
            neighbour_index = int(neighbour_index)
            if neighbour_index == row_index:
                continue
            similarity = float(1.0 - distance)
            edges.append((row_index, neighbour_index, similarity))
    return edges


def summarise_similarity_graph(rows, edges, threshold):
    """Summarise connected components after applying one similarity threshold."""
    if not rows:
        raise ValueError("Cannot audit an empty row set.")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between zero and one.")

    union_find = UnionFind(len(rows))
    selected_edges = []

    for left, right, similarity in edges:
        if not (0 <= left < len(rows) and 0 <= right < len(rows)):
            raise ValueError("An edge index is outside the supplied row range.")
        if similarity >= threshold:
            union_find.union(left, right)
            selected_edges.append((left, right, similarity))

    components = defaultdict(list)
    for index in range(len(rows)):
        components[union_find.find(index)].append(index)

    component_sizes = [
        len(indices)
        for indices in components.values()
        if len(indices) > 1
    ]
    non_singleton_components = [
        indices for indices in components.values() if len(indices) > 1
    ]

    cross_split_components = 0
    cross_split_rows = 0
    mixed_label_components = 0
    cross_language_components = 0
    component_profiles = []

    for indices in non_singleton_components:
        members = [rows[index] for index in indices]
        splits = {row["split"] for row in members}
        labels = {row["label"] for row in members}
        languages = {row["language"] for row in members}

        if len(splits) > 1:
            cross_split_components += 1
            cross_split_rows += len(indices)
        if len(labels) > 1:
            mixed_label_components += 1
        if len(languages) > 1:
            cross_language_components += 1

        component_profiles.append(
            {
                "rows": len(indices),
                "partitions": len(splits),
                "labels": len(labels),
                "languages": len(languages),
            }
        )

    cross_split_edges = 0
    cross_label_edges = 0
    cross_language_edges = 0
    for left, right, _similarity in selected_edges:
        left_row = rows[left]
        right_row = rows[right]
        cross_split_edges += int(left_row["split"] != right_row["split"])
        cross_label_edges += int(left_row["label"] != right_row["label"])
        cross_language_edges += int(
            left_row["language"] != right_row["language"]
        )

    sorted_sizes = sorted(component_sizes)
    p90_index = (
        min(len(sorted_sizes) - 1, int(np.ceil(0.90 * len(sorted_sizes))) - 1)
        if sorted_sizes
        else None
    )
    largest_profiles = sorted(
        component_profiles,
        key=lambda item: item["rows"],
        reverse=True,
    )[:10]

    return {
        "threshold": float(threshold),
        "directed_knn_edges_at_or_above_threshold": len(selected_edges),
        "cross_split_knn_edges": int(cross_split_edges),
        "cross_label_knn_edges": int(cross_label_edges),
        "cross_language_knn_edges": int(cross_language_edges),
        "similarity_connected_components": len(components),
        "non_singleton_components": len(non_singleton_components),
        "rows_in_non_singleton_components": int(sum(component_sizes)),
        "fraction_rows_in_non_singleton_components": round(
            sum(component_sizes) / len(rows),
            4,
        ),
        "median_non_singleton_component_size": (
            float(np.median(sorted_sizes)) if sorted_sizes else 0.0
        ),
        "p90_non_singleton_component_size": (
            int(sorted_sizes[p90_index]) if p90_index is not None else 0
        ),
        "largest_non_singleton_component_size": (
            max(sorted_sizes) if sorted_sizes else 0
        ),
        "components_spanning_train_validation": int(cross_split_components),
        "rows_in_components_spanning_train_validation": int(cross_split_rows),
        "components_with_multiple_labels": int(mixed_label_components),
        "components_with_multiple_languages": int(cross_language_components),
        "largest_component_profiles": largest_profiles,
    }


def build_report(rows, edges):
    return {
        "experiment": "approximate_train_validation_template_family_audit",
        "rows": len(rows),
        "train_rows": sum(row["split"] == "train" for row in rows),
        "validation_rows": sum(row["split"] == "validation" for row in rows),
        "test_partition_read": False,
        "model_trained": False,
        "model_artifact_modified": False,
        "method": {
            "representation": "saved model character TF-IDF",
            "neighbours_per_row": NEIGHBOUR_COUNT,
            "similarity": "cosine",
            "graph": "undirected connected components from directed top-K neighbour edges",
            "thresholds": list(SIMILARITY_THRESHOLDS),
            "approximate": True,
        },
        "results": [
            summarise_similarity_graph(rows, edges, threshold)
            for threshold in SIMILARITY_THRESHOLDS
        ],
        "limitations": [
            "Only train and validation partitions are read; the initial test partition is not read.",
            "Only each row's top-K neighbours are used, so the graph is approximate.",
            "Connected components can join rows through similarity chains.",
            "Character similarity can reflect language/script and common phrases, not only shared templates.",
            "Thresholds are exploratory and do not define verified campaign families.",
            "This is not an independent performance evaluation or proof of data leakage.",
        ],
    }


def main():
    if not MODEL_PATH.is_file():
        raise SystemExit(
            f"Model artifact not found: {MODEL_PATH}. "
            "Run data/train_multilingual_baseline.py first."
        )

    try:
        train_rows = read_split(SPLIT_DIRECTORY / "train.csv")
        validation_rows = read_split(SPLIT_DIRECTORY / "validation.csv")
        model = joblib.load(MODEL_PATH)

        combined_rows = [
            {**row, "split": "train"}
            for row in train_rows
        ] + [
            {**row, "split": "validation"}
            for row in validation_rows
        ]

        exact_texts = [row["model_text_sha256"] for row in combined_rows]
        if len(exact_texts) != len(set(exact_texts)):
            raise ValueError("Exact masked-text duplicates found across train/validation.")

        features = model.named_steps["tfidf"].transform(
            [row["text"] for row in combined_rows]
        )
        edges = build_knn_edges(features)
        report = build_report(combined_rows, edges)
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Template-family audit failed: {error}") from error

    ARTIFACT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)

    print("SOUL — approximate template-family audit")
    print("Train rows:", len(train_rows))
    print("Validation rows:", len(validation_rows))
    print("Test partition read: no")
    print("Model trained: no")
    print("Model artifact modified: no")
    print("Character-TF-IDF rows:", len(combined_rows))
    print("Directed neighbour edges:", len(edges))

    for result in report["results"]:
        print(f"\nSIMILARITY THRESHOLD >= {result['threshold']:.2f}")
        print("  Non-singleton components:", result["non_singleton_components"])
        print(
            "  Rows in non-singleton components:",
            result["rows_in_non_singleton_components"],
            f"({result['fraction_rows_in_non_singleton_components']:.1%})",
        )
        print("  Median component size:", result["median_non_singleton_component_size"])
        print("  P90 component size:", result["p90_non_singleton_component_size"])
        print("  Largest component:", result["largest_non_singleton_component_size"])
        print(
            "  Components spanning train/validation:",
            result["components_spanning_train_validation"],
        )
        print(
            "  Components with mixed labels/languages:",
            result["components_with_multiple_labels"],
            "/",
            result["components_with_multiple_languages"],
        )
        print(
            "  Cross-split / cross-label / cross-language edges:",
            result["cross_split_knn_edges"],
            "/",
            result["cross_label_knn_edges"],
            "/",
            result["cross_language_knn_edges"],
        )

    print("\nAggregate report saved locally:", REPORT_PATH)
    print(
        "\nInterpretation: approximate similarity components are candidate "
        "template families, not verified campaign identities or proof of leakage."
    )


if __name__ == "__main__":
    main()
