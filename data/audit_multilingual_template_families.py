"""Approximate template-family audit across train and validation only.

This audit creates a bipartite character-TF-IDF k-nearest-neighbour graph:
each validation row is connected to its closest training rows. It does not
compare every pair in the combined 10k+ corpus, read the initial holdout test,
train a classifier, or change model artifacts.

Run from repository root:
    python data/audit_multilingual_template_families.py

The graph is approximate because only each validation row's closest K training
neighbours are considered. Similarity thresholds are diagnostic heuristics.
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


def build_knn_edges(
    train_matrix,
    validation_matrix,
    neighbour_count=NEIGHBOUR_COUNT,
):
    """Return validation-to-training top-K edges with combined row indices."""
    train_count = train_matrix.shape[0]
    validation_count = validation_matrix.shape[0]

    if train_count < 1 or validation_count < 1:
        raise ValueError("Train and validation matrices must both be non-empty.")
    if neighbour_count < 1:
        raise ValueError("neighbour_count must be at least one.")

    requested = min(neighbour_count, train_count)
    model = NearestNeighbors(
        n_neighbors=requested,
        metric="cosine",
        algorithm="brute",
        n_jobs=1,
    )
    model.fit(train_matrix)
    distances, indices = model.kneighbors(validation_matrix)

    edges = []
    for validation_index in range(validation_count):
        combined_validation_index = train_count + validation_index
        for distance, train_index in zip(
            distances[validation_index],
            indices[validation_index],
        ):
            similarity = float(1.0 - distance)
            edges.append(
                (combined_validation_index, int(train_index), similarity)
            )
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

    cross_label_edges = 0
    cross_language_edges = 0
    for left, right, _similarity in selected_edges:
        left_row = rows[left]
        right_row = rows[right]
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
        "validation_to_train_knn_edges_at_or_above_threshold": len(selected_edges),
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


def build_report(train_rows, validation_rows, edges):
    combined_rows = [
        {**row, "split": "train"}
        for row in train_rows
    ] + [
        {**row, "split": "validation"}
        for row in validation_rows
    ]
    return {
        "experiment": "approximate_train_validation_template_family_audit",
        "rows": len(combined_rows),
        "train_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "test_partition_read": False,
        "model_trained": False,
        "model_artifact_modified": False,
        "method": {
            "representation": "saved model character TF-IDF",
            "neighbours_per_validation_row": NEIGHBOUR_COUNT,
            "similarity": "cosine",
            "graph": "bipartite connected components from validation-to-train top-K edges",
            "thresholds": list(SIMILARITY_THRESHOLDS),
            "approximate": True,
        },
        "results": [
            summarise_similarity_graph(
                combined_rows,
                edges,
                threshold,
            )
            for threshold in SIMILARITY_THRESHOLDS
        ],
        "limitations": [
            "Only train and validation partitions are read; the initial test partition is not read.",
            "Only each validation row's top-K training neighbours are used, so the graph is approximate.",
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

        train_hashes = {row["model_text_sha256"] for row in train_rows}
        validation_hashes = {row["model_text_sha256"] for row in validation_rows}
        if train_hashes & validation_hashes:
            raise ValueError("Exact masked-text duplicates found across train/validation.")

        vectorizer = model.named_steps["tfidf"]
        train_matrix = vectorizer.transform(
            [row["text"] for row in train_rows]
        )
        validation_matrix = vectorizer.transform(
            [row["text"] for row in validation_rows]
        )
        edges = build_knn_edges(train_matrix, validation_matrix)
        report = build_report(train_rows, validation_rows, edges)
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
    print("Top-K validation-to-train edges:", len(edges))

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
            "  Cross-label / cross-language edges:",
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
